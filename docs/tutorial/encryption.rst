Hintergrund zu den Verschlüsselungsdaten
========================================

In der Datenbank von edupsyadmin auf deinem Rechner sind bestimmte
personenbezogene Daten verschlüsselt und werden bei der Ausführung eines
Befehls von edupsyadmin vorrübergehend entschlüsselt (alle Variablen, deren
Name auf "_encr" endet, s. :doc:`../clients_model`).

.. warning::

   Die Datenbank ist verschlüsselt, aber **nicht** die PDF-Formular-Dateien,
   die mit edupsyadmin befüllt werden! Daher sollte der Speicher verschlüsselt
   sein: `Link zur Erklärung des BSI
   <https://www.bsi.bund.de/DE/Themen/Verbraucherinnen-und-Verbraucher/Informationen-und-Empfehlungen/Cyber-Sicherheitsempfehlungen/Daten-sichern-verschluesseln-und-loeschen/Datenverschluesselung/Soft-und-hardwaregestuetzte-Verschluesselung/soft-und-hardwaregestuetzte-verschluesselung_node.html#doc504660bodyText2>`_

Standard Backends
-----------------

edupsyadmin verwendet ``keyring``, um die Verschlüsselungsdaten zu speichern.
``keyring`` hat mehrere Backends. Unter Windows ist der Standard Windows
Credential Manager (Deutsch: Anmeldeinformationsverwaltung), auf macOS Keychain
(Deutsch: Schlüsselbund).

Wenn du den Windows Credential Manager verwendest, sollte dein Rechner mit
einem guten Passwort geschützt und nur für dich zugänglich sein, denn jeder,
der die Login Daten für deinen Rechner kennt, hat damit Zugriff auf deine
Anmeldeinformationsverwaltung und auf die dort gespeicherten
Verschlüsselungsdaten für edupsyadmin. Das Bitwarden Backend entschlüsselt
nicht mit dem Login des Betriebsystems (s.u.).

Standardmäßig gilt auch für die macOS Keychain, dass ein Nutzer mit dem Login
in das Betriebsystem Zugriff auf die Zugangsdaten hat, wobei hier ein vom Login
separates Password für Keychain gesetzt werden kann.

Bitwarden Backend
-----------------

Eine für alle Betriebssysteme mögliche Alternative ist die Bitwarden CLI. Sie
erfordert vor jeder Nutzung von edupsyadmin, dass der Zugang zum Password für
die Sitzung entschlüsselt wird. Dafür musst du:

- ein Bitwarden-Konto anlegen: `<https://bitwarden.com>`_
- die Bitwarden CLI installieren: `<https://bitwarden.com/help/cli/>`_
- edupsyadmin mit dem optionalen Paket bitwarden-keyring installieren:

.. code-block :: console

  uv tool install --with bitwarden-keyring edupsyadmin

- dich einmalig in der Shell (z.B. Powershell über das Windows Terminal)
  einloggen:

.. code-block :: console

  bw login

- vor jeder Sitzung Bitwarden mit dem für Bitwarden gesetzten
  Passwort entschlüsseln

.. code-block :: console

  bw unlock

- den von ``bw unlock`` generierten Sitzungsschlüssel in die Shell  (``export
  BW_SESSION=...`` für Bash oder ``$env:BW_SESSION=...`` für Powershell)

- nach der Sitzung den Zugang wieder verschlüsseln mit ``bw lock``
