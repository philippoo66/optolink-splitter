# MQTT /set Topics - User-Friendly Write Feature

## Overview

Starting with this version, you can write values to your Viessmann heating system using simple MQTT topics instead of the complex command syntax.

For each datapoint that is published (e.g., `vito/c1_temp_room_setpoint`), you can now write to it by publishing to the `/set` topic: `vito/c1_temp_room_setpoint/set`.

**Key benefit:** You can use the same format for writing as you see when reading! For example:
- If a value is published as `ON` or `OFF`, you can write `ON` or `OFF`
- If a value is published as `18.5`, you can write `18.5`
- No need for complex command strings or manual scaling calculations

## How It Works

### Topic Format

```
{mqtt_topic}/{datapoint_name}/set
```

For example, if your `mqtt_topic` is configured as `vito`:
- Read topic: `vito/hk1_normal_temperature` (publishes: `20.5`)
- Write topic: `vito/hk1_normal_temperature/set` (accepts: `21.0`)

### Supported Value Formats

The /set topic automatically detects the datapoint's format and converts your value appropriately:

#### 1. Boolean Values (`'onoff'`, `'offon'`, `'bool'`, `'boolinv'`)

For datapoints configured with boolean-like formats:

**Poll list example:**
```python
("hk1_pump", 0x048D, 1, 'onoff'),
```

**Writing:**
```bash
# Using mosquitto_pub
mosquitto_pub -h your-broker -t "vito/hk1_pump/set" -m "ON"
mosquitto_pub -h your-broker -t "vito/hk1_pump/set" -m "OFF"

# Also accepts: 1, 0, true, false, yes, no (case-insensitive)
```

#### 2. Numeric Values with Scaling

For datapoints with numeric scaling (temperature, pressure, etc.):

**Poll list example:**
```python
("hk1_normal_temperature", 0x2000, 2, 0.1, False),
```

**Writing:**
```bash
# Set temperature to 21.5°C
mosquitto_pub -h your-broker -t "vito/hk1_normal_temperature/set" -m "21.5"

# Set to 20°C
mosquitto_pub -h your-broker -t "vito/hk1_normal_temperature/set" -m "20"
```

The system automatically:
- Applies reverse scaling (divides by the scale factor)
- Converts to appropriate byte format
- Handles signed/unsigned values correctly

#### 3. Raw Integer Values

For datapoints without special formatting:

**Poll list example:**
```python
("hk1_mode", 0xB000, 1, 1, False),
```

**Writing:**
```bash
# Set mode to value 2
mosquitto_pub -h your-broker -t "vito/hk1_mode/set" -m "2"

# Also accepts hex format
mosquitto_pub -h your-broker -t "vito/hk1_mode/set" -m "0x02"
```

## Examples

### Example Setting Hot Water Temperature

**Poll list configuration:**
```python
("hotwater_temperature", 0x6300, 1, 1, False),
```

**Reading the current value:**
```bash
# Subscribe to read topic
mosquitto_sub -h your-broker -t "vito/hotwater_temperature"
# Receives: 45
```

**Writing a new value:**
```bash
# Classic way:
mosquitto_pub -h your-broker -t "vito/cmnd" -m "write;0x6300;1;50"

# Via set topic:
mosquitto_pub -h your-broker -t "vito/hotwater_temperature/set" -m "50"
```

## Home Assistant Integration

The /set topics work seamlessly with Home Assistant's MQTT integration:

```yaml
# configuration.yaml
mqtt:
  climate:
    - name: "Heating Circuit 1"
      mode_command_topic: "vito/hk1_mode/set"
      temperature_command_topic: "vito/hk1_normal_temperature/set"
      temperature_state_topic: "vito/hk1_normal_temperature"
      current_temperature_topic: "vito/hk1_temperature"
      # ... other configuration

  switch:
    - name: "Circulation Pump"
      command_topic: "vito/circulation_pump/set"
      state_topic: "vito/circulation_pump"
      payload_on: "ON"
      payload_off: "OFF"
```

## Technical Details

### How Values Are Converted

The system performs the following steps when receiving a /set message:

1. **Extract datapoint name** from the topic path
2. **Lookup datapoint configuration** in the poll_list
3. **Parse the value** based on the datapoint's scale/type:
   - Boolean types: Accept ON/OFF, true/false, 1/0
   - Numeric types: Apply reverse scaling
   - Integer types: Parse as-is
4. **Convert to bytes** with appropriate length and signedness
5. **Generate write command** in the format expected by the system
6. **Execute write** through the standard command queue

### Logging

The system logs /set topic operations:
```
INFO: Received /set request: hk1_normal_temperature = 21.0
INFO: Generated write command: write;0x2000;2;210
```

Check your logs to verify write operations are being processed correctly.

## Limitations

1. **Datapoint must be in poll_list**: Only datapoints defined in your poll_list can be written via /set topics
2. **Write permissions**: Some datapoints are read-only at the device level
3. **Format matching**: The value format must match what the datapoint expects
4. **No ByteBit Filter**: ByteBit filter datapoints are not supported for writing via /set topics
5. **String types**: UTF-8/UTF-16 string types are not writable via /set topics

## Troubleshooting

### Value Not Changing

1. **Check logs** for error messages
2. **Verify datapoint is writable** on your device
3. **Confirm datapoint name** matches exactly what's in poll_list
4. **Check value format** - ensure it matches the datapoint type

### Topic Not Working

1. **Verify MQTT connection** - check that optolinkvs2_switch.py is running
2. **Check topic name** - must match `{mqtt_topic}/{dpname}/set`
3. **Ensure poll_list is loaded** - datapoint must exist in poll_list

### Permission Errors

Some datapoints may be read-only on your specific Viessmann device. This is a device limitation, not a software limitation.

## Migration Guide

If you have existing automation using the old command syntax, you can migrate gradually:

**Before:**
```yaml
# Home Assistant automation
action:
  - service: mqtt.publish
    data:
      topic: "vito/cmnd"
      payload: "write;0x2000;2;210"
```

**After:**
```yaml
# Home Assistant automation
action:
  - service: mqtt.publish
    data:
      topic: "vito/hk1_normal_temperature/set"
      payload: "21.0"
```

The old method continues to work, so you can migrate at your own pace.

## Additional Resources

- [Old Command Syntax Documentation](https://github.com/philippoo66/optolink-splitter/wiki/010-Command-Syntax)
- [Poll List Configuration](https://github.com/philippoo66/optolink-splitter/wiki/350-Poll-Configuration-Samples)
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt)
