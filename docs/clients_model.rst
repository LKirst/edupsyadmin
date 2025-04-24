Dokumentation der Datenbank
===========================

Unten beschriebene Variablen der Datenbank, die auf "_encr" enden
("_encr" für *encrypted*, verschlüsselt), können ohne die Endung
"_encr" in Formularen verwendet werden.

.. autoclass:: edupsyadmin.api.clients.Client
   :members:

Auf Grundlage der Daten der Datenbank werden mit der Funktion
`add_convenience_data` folgende  weitere Variablen zusammengesetzt, die auch in
Formularen verwendet werden können:

.. automodule:: edupsyadmin.api.add_convenience_data
   :members: add_convenience_data
