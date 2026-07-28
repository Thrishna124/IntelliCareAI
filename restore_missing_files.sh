#!/bin/bash

OLD="/Users/thrishna/Desktop/Critical_Django_project/docspot"
NEW="$HOME/Desktop/IntelliCareAI"

APPS=(
    heart
    kidney
    liver
    lungs
    lung_cancer
    pancreas
    fitness
)

echo "Restoring missing support files..."

for APP in "${APPS[@]}"; do
    echo "-------------------------------------"
    echo "Processing $APP"

    # Copy only if missing
    for FILE in admin.py apps.py forms.py models.py tests.py; do
        if [ -f "$OLD/$APP/$FILE" ] && [ ! -f "$NEW/$APP/$FILE" ]; then
            cp "$OLD/$APP/$FILE" "$NEW/$APP/"
            echo "Copied $APP/$FILE"
        fi
    done

    # migrations/__init__.py
    if [ -f "$OLD/$APP/migrations/__init__.py" ]; then
        mkdir -p "$NEW/$APP/migrations"
        if [ ! -f "$NEW/$APP/migrations/__init__.py" ]; then
            cp "$OLD/$APP/migrations/__init__.py" "$NEW/$APP/migrations/"
            echo "Copied $APP/migrations/__init__.py"
        fi
    fi

    # static folder
    if [ -d "$OLD/$APP/static" ] && [ ! -d "$NEW/$APP/static" ]; then
        cp -R "$OLD/$APP/static" "$NEW/$APP/"
        echo "Copied $APP/static"
    fi
done

echo
echo "====================================="
echo "Recovery complete!"
echo "====================================="
