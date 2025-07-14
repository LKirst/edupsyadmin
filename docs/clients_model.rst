Dokumentation der Datenbank
===========================

Unten beschriebene Variablen der Datenbank, die auf "_encr" enden sind in der
Datenbank verschlüsselt und werden bei jedem Abruf für die Verarbeitung
entschlüsselt ("_encr" für *encrypted*, verschlüsselt).

.. autoclass:: edupsyadmin.db.clients.Client
   :members:

Auf Grundlage der Daten der Datenbank werden mit der Funktion
``add_convenience_data`` folgende  weitere Variablen zusammengesetzt, die auch in
Formularen verwendet werden können:

.. automodule:: edupsyadmin.api.add_convenience_data
   :members: add_convenience_data
