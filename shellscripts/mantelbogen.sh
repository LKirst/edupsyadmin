edupsy_admin -w DEBUG create_documentation $1 \
    ~/Templates/Beratung/LK_Mantelbogen.pdf

python ~/bin/libadmin/pdf_two_pages_per_sheet.py -p "$1_LK_Mantelbogen.pdf" --flatten

rm "$1_LK_Mantelbogen.pdf"
