Dokumentation erstellen
=======================

Jetzt kommt der Schritt, bei dem ``edupsyadmin`` richtig Zeit spart! Die
Anwendung kann die Daten, die du soeben eingegeben hast, nutzen, um
PDF-Formulare oder andere Dokumente automatisch auszufüllen.

Ablauf
------

#.  **Klient*in auswählen**: Wähle in der TUI deine*n eben erstellte*n
    Klient*in aus der Liste aus. Die Details sollten rechts erscheinen.
#.  **Dialog öffnen**: Drücke das Tastenkürzel :kbd:`Strg+f`. Es öffnet sich der
    Dialog "Formulare ausfüllen".

    .. image:: ../../test/edupsyadmin/tui/__snapshots__/test_fill_form_tui/test_initial_layout.svg
       :alt: Dialog zum Ausfüllen von Formularen

#.  **Formulare auswählen**: In diesem Dialog hast du zwei Möglichkeiten,
    Formulare auszuwählen:

    - **Formular-Sätze (links)**: Wähle einen oder mehrere vordefinierte
      "Formular-Sätze" aus. Diese Sätze werden in der
      :doc:`Konfiguration <../tutorial/configuration>` festgelegt und fassen
      häufig benötigte Formulare zusammen.
    - **Dateiauswahl (rechts)**: Navigiere durch das Dateisystem und wähle
      einzelne PDF- oder Markdown-Dateien aus. Du kannst den Startpfad oben im
      Eingabefeld ändern.

#.  **Ausfüllen starten**: Klicke auf den Button "Fill Form(s)" oder drücke die
    entsprechende Taste, um den Vorgang zu starten. ``edupsyadmin`` nimmt sich
    dann die ausgewählten Vorlagen und füllt sie mit den Daten des Klienten.

Erstellen von Formularen
------------------------

Damit ``edupsyadmin`` deine Formulare korrekt ausfüllen kann, müssen die
Platzhalter in deinen Vorlagen einem bestimmten Muster folgen. Die Platzhalter
entsprechen den Spaltennamen in der Datenbank.

Es gibt zwei Möglichkeiten für Formulare: PDF-Formulare und
Markdown-Liquid-Formulare

Beispiel für ein PDF-Formular mit Libreoffice Writer erstellt und als PDF
exportiert:

#. Libreoffice Writer öffnen.

#. Über Ansicht - Symbolleisten - Formular-Steuerelemente die
   Formular-Steuerelemente anzeigen.

#. Ein Textfeld hinzugen für den Vornamen mit dem Feldnamen ``first_name_encr``.

#. Ein Textfeld hinzufügen für das Geburtsdatum: ``birthday_encr``.

#. Über Datei - Expoertieren als - Als PDF exportieren ... die Datei als PDF
   exportieren. In dem Fenster das sich öffnet, die Option aktivieren
   "PDF-Formular erzeugen"

Für Markdown-Vorlagen verwendest du Platzhalter im Text mit dem Namen der
Variable in doppelten geschwungenen Klammern:

.. code-block:: markdown

   # Protokoll

   **Name**: {{ last_name_encr }}, {{ first_name_encr }}
   **Geboren am**: {{ birthday_encr }}
