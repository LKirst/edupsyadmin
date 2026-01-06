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
   :emphasize-lines: 10-21

    $ edupsyadmin --help
    usage: edupsyadmin [-h] [-v] [-w WARN]
                       {info,edit_config,new_client,set_client,create_documentation,get_clients,flatten_pdfs,mk_report,taetigkeitsbericht,delete_client} ...

    options:
      -h, --help            show this help message and exit
      -v, --version         print version and exit
      -w, --warn WARN       logger warning level [WARN]

    subcommands:
      {info,edit_config,new_client,set_client,create_documentation,get_clients,flatten_pdfs,mk_report,taetigkeitsbericht,delete_client}
        info                Get useful information for debugging
        edit_config         Edit app configuration
        new_client          Add a new client
        set_client          Change values for one or more clients
        create_documentation
                            Fill a pdf form or a text file with a liquid template
        get_clients         Show clients overview or single client
        flatten_pdfs        Flatten pdf forms (experimental)
        taetigkeitsbericht  Create a PDF output for the Taetigkeitsbericht (experimental)
        delete_client       Delete a client in the database


Die Hilfe zeigt uns, dass wir den edupsyadmin Befehl mit verschiedenen
Unterbefehlen zusammen ausführen (z.B. ``edupsyadmin info``, ``edupsyadmin
new_client``, ``edupsyadmin create_documentation``).

Beispiel 2: Hilfe für einen Unterbefehl anzeigen
------------------------------------------------

Um die Hilfe für einen bestimmten Unterbefehl anzuzeigen, verwende den Befehl
wie folgt:

.. code-block:: console

    $ edupsyadmin create_documentation --help

Dies wird dir die Optionen und Argumente für den ``create_documentation``
Unterbefehl anzeigen:

.. code-block:: console
   :emphasize-lines: 2,6,9

    $ edupsyadmin create_documentation --help
    usage: edupsyadmin create_documentation [-h] client_id [client_id ...] [--form_set FORM_SET] [--form_paths FORM_PATH ...]

    Fill a pdf form or a text file with a liquid template. Either --form_set or --form_paths must be provided.

    positional arguments:
      client_id

    options:
      -h, --help            show this help message and exit
      --form_set FORM_SET   name of a set of file paths defined in the config file
      --form_paths [FORM_PATHS ...]
                            form file paths

Die Hilfe zeigt ``positional arguments``  und ``options``. Die positional
arguments sind Argumente, die du dem Unterbefehl in einer bestimmten
Reihenfolge übergeben musst. Die options sind hingegen optionale Parameter, mit
denen du das Verhalten des Unterbefehls beeinflussen kannst. Insgesamt siehst
du hier, dass der Unterbefehl "create_documentation" ein positional argument
(client_id) und mehrere optionale Optionen akzeptiert.
Argumente oder Optionen, die bei ``usage:`` in eckigen Klammern stehen, sind
optional. (Bei ``create_documentation`` gibt es noch die Besonderheit, dass
entweder ein ``form_set`` oder mindestens ein ``form_path`` angegeben werden
müssen.)
