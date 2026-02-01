Hilfe Funktion
==============

.. tip::

    Ich halte es für hilfreich, diesen Abschnitt als erstes zu lesen. Wenn
    er dich aber verwirrt, gehe erst zu den konreten Anwendungen und komme
    später zu diesem Kapitel zurück. Dann wird deutlicher sein, wofür die
    Hilfe Funktion nützlich ist.

Die ``--help`` Option ist eine nützliche Funktion, die dir dabei hilft, die
verschiedenen Befehle und Optionen des edupsyadmin-Tools zu verstehen.

Beispiel 1: Allgemeine Hilfe anzeigen
-------------------------------------

Um die allgemeine Hilfe für das edupsyadmin-Tool anzuzeigen, führe folgenden
Befehl aus:

.. code-block:: console

    $ edupsyadmin --help

Dies wird dir eine Übersicht über alle verfügbaren Optionen und Unterbefehle
anzeigen. Im Beispiel unten, sind die möglichen Unterbefehle markiert.

.. code-block:: console
   :emphasize-lines: 10-25

    $ edupsyadmin --help
    usage: edupsyadmin [-h] [-v] [-w WARN]
                   {create-documentation,delete-client,edit-config,flatten-pdfs,get-clients,info,migrate-encryption,mk-report,new-client,set-client,setup-demo,taetigkeitsbericht,tui} ...

    options:
      -h, --help            show this help message and exit
      -v, --version         print version and exit
      -w, --warn WARN       logger warning level [WARN]

    subcommands:
      {create-documentation,delete-client,edit-config,flatten-pdfs,get-clients,info,migrate-encryption,mk-report,new-client,set-client,setup-demo,taetigkeitsbericht,tui}
        create-documentation
                            Fill a pdf form or a text file with a liquid template
        delete-client       Delete a client in the database
        edit-config         Edit app configuration
        flatten-pdfs        Flatten pdf forms (experimental)
        get-clients         Show clients overview or single client
        info                Get useful information for debugging
        migrate-encryption  Migrate database to new encryption system
        mk-report           Create a report for a given test type. (experimental)
        new-client          Add a new client
        set-client          Change values for one or more clients
        setup-demo          Create a sandboxed demo environment.
        taetigkeitsbericht  Create a PDF output for the Taetigkeitsbericht (experimental)
        tui                 Start the TUI


Die Hilfe zeigt uns, dass wir den edupsyadmin Befehl mit verschiedenen
Unterbefehlen zusammen ausführen (z.B. ``edupsyadmin info``, ``edupsyadmin
new-client``, ``edupsyadmin create-documentation``).

Beispiel 2: Hilfe für einen Unterbefehl anzeigen
------------------------------------------------

Um die Hilfe für einen bestimmten Unterbefehl anzuzeigen, verwende den Befehl
wie folgt:

.. code-block:: console

    $ edupsyadmin create-documentation --help

Dies wird dir die Optionen und Argumente für den ``create-documentation``
Unterbefehl anzeigen:

.. code-block:: console
   :emphasize-lines: 2,6,9

    $ edupsyadmin create-documentation --help
    usage: edupsyadmin create-documentation [-h] [--tui] [--form_set FORM_SET] [--form_paths [FORM_PATHS ...]] [--inject_data [INJECT_DATA ...]] [client_id ...]

    Fill a pdf form or a text file with a liquid template. Use --tui for interactive mode, or provide client_id and form details for direct creation.

    positional arguments:
      client_id

    options:
      -h, --help            show this help message and exit
      --tui                 Open TUI for interactive form filling.
      --form_set FORM_SET   name of a set of file paths defined in the config file
      --form_paths [FORM_PATHS ...]
                            form file paths
      --inject_data [INJECT_DATA ...]
                            key-value pairs in the format 'key=value'; this option can be used to override existing key=value pairs or add new key=value pairs

    Examples:
    # Open the TUI to interactively fill a form
    edupsyadmin create_documentation --tui

    # Fill a PDF form for client with ID 1 using a form set named 'MyFormSet'
    edupsyadmin create_documentation 1 --form_set MyFormSet

    # Fill a text file for client with ID 2 using a specific form path
    edupsyadmin create_documentation 2 --form_paths "./path/to/template.txt"

    # Fill a form for client with ID 3, injecting custom data
    edupsyadmin create_documentation 3 --form_paths "./path/to/form.pdf" \
      --inject_data "key1=value1" "key2=value2"

Die Hilfe zeigt ``positional arguments``  und ``options``. Die positional
arguments sind Argumente, die du dem Unterbefehl in einer bestimmten
Reihenfolge übergeben musst. Die options sind hingegen optionale Parameter, mit
denen du das Verhalten des Unterbefehls beeinflussen kannst. Insgesamt siehst
du hier, dass der Unterbefehl "create-documentation" ein positional argument
(client_id) und mehrere optionale Optionen akzeptiert.
Argumente oder Optionen, die bei ``usage:`` in eckigen Klammern stehen, sind
optional. (Bei ``create-documentation`` gibt es noch die Besonderheit, dass
entweder ein ``form_set`` oder mindestens ein ``form_path`` angegeben werden
müssen.)
