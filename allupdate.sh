#!/bin/bash

# ausführen per
# & "C:\Program Files\Git\bin\sh.exe" ./allupdate.sh

echo "Starte das Update aller Branches..."
git fetch --all
for branch in $(git branch -r | grep -v '\->'); do
    local_branch="${branch#origin/}"
    echo "Wechsle zu Branch $branch und aktualisiere..."

    # Prüfen, ob der Branch bereits lokal existiert
    if git show-ref --verify --quiet "refs/heads/$local_branch"; then
        # Wenn der Branch existiert, wechsle zu ihm
        git checkout "$local_branch"
    else
        # Wenn der Branch nicht existiert, erstelle ihn
        git checkout --track "$branch"
    fi

    # Aktualisiere den Branch
    git pull
done
echo "Update abgeschlossen!"
