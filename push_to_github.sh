#!/bin/bash

# Script para subir el proyecto a GitHub
# Usuario de GitHub: acesarsr
# Repositorio: XSIAM-Migration-Assistant

echo "Configurando repositorio remoto..."
git remote add origin https://github.com/acesarsr/XSIAM-Migration-Assistant.git

echo "Subiendo a GitHub..."
git push -u origin main

echo "✅ Proyecto subido exitosamente a GitHub!"
echo "Visita: https://github.com/acesarsr/XSIAM-Migration-Assistant"
