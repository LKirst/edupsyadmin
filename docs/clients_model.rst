Dokumentation der Datenbank
===========================

Unten beschriebene Variablen der Datenbank, die auf "_encr" enden sind in der
Datenbank verschlüsselt und werden bei jedem Abruf für die Verarbeitung
entschlüsselt ("_encr" für *encrypted*, verschlüsselt).

.. autoclass:: edupsyadmin.db.clients.Client
   :members:

Auf Grundlage der Daten der Datenbank werden mit der Klasse
``ClientView`` folgende weitere Variablen zusammengesetzt, die
auch in Formularen verwendet werden können:

.. autoclass:: edupsyadmin.api.client_view.ClientView
   :members:
   :exclude-members: record
