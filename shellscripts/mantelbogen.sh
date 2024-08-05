edupsy_admin -w DEBUG -c ~/bin/edupsy_admin/etc/config.yml\
    create_documentation lukas.liebermann $1\
    ~/Templates/Beratung/LK_Mantelbogen_2023.pdf

python ~/bin/libadmin/pdf_two_pages_per_sheet.py -p "$1_LK_Mantelbogen_2023.pdf" --flatten

rm "$1_LK_Mantelbogen_2023.pdf" -i 
