.. edupsyadmin documentation master file, created by
   sphinx-quickstart on Sat Mar  1 10:59:37 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dokumentation für edupsyadmin
=============================

Über edupsyadmin
----------------

Edupsyadmin bietet Werkzeuge, um Schulpsychologen bei ihrer Dokumentation zu
unterstützen.

- Dokumentation: https://edupsyadmin.readthedocs.io

- Quellcode: https://github.com/LKirst/edupsyadmin

- Issues: https://github.com/LKirst/edupsyadmin/issues

.. tip::

    Unter dem oben genannten Link zu "Issues" kannst du berichten, wenn du
    Probleme mit edupsyadmin hast oder Wünsche zu Änderungen an der App. Bitte
    gebe bei Fragen zu Problemen immer die Version von edupsyadmin an, die du
    verwendest.

Warum edupsyadmin?
------------------

edupsyadmin beschleunigt sowohl die Dokumentation einzelner Beratungsfälle
als auch die Erstellung des Tätigkeitsberichts.

Schulpsychologen müssen dieselben Daten immer wieder für unterschiedliche
Formulare abschreiben. Zum Beispiel müssen teils dieselben Daten aufgeführt
werden auf

- dem Mantelbogen der schulpsychologischen Dokumentation

- der schulpsychologischen Stellungnahme

- dem Anschreiben zur Stellungnahme

- dem Vordruck der Gewährung der Schulleitung

Mit edupsyadmin lassen sich die Daten aus Webuntis importieren oder
einmalig händisch eingeben. Auf dieser Grundlage lassen sich dann
`PDF-Formulare
<https://de.wikipedia.org/wiki/Portable_Document_Format#Formularprozesse>`_
mit einem Befehl ausfüllen. Da das Abschreiben ausbleibt, werden so auch
Fehlerquellen minimiert.

edupsyadmin schätzt aus den gespeicherten Daten das Datum, an dem die Akten
vernichtet werden können (3 Jahre nach Ende des Besuchs der Schule), sodass
dieses Datum auf dem Mantelbogen vermerkt werden kann.

Zu jedem mit edupsyadmin gespeicherten Fall kann ein
Tätigkeitsbericht-Schlüsselbegriff und die Anzahl der auf den Fall verwendeten
Stunden gespeichert werden. Dann kann edupsyadmin die Daten berechnen, die der
Tätigkeitsbericht verlangt.

.. toctree::
   :maxdepth: 2
   :caption: Tutorial

   tutorial/installation
   tutorial/helpfunction
   tutorial/addingclients
   tutorial/creatingdocumentation
   tutorial/update

.. toctree::
   :maxdepth: 2
   :caption: Datenbank und Keywords

   clients_model
   taetigkeitsbericht_keywords


Autor
-----

edupsyadmin wurde von Lukas Liebermann geschrieben.
