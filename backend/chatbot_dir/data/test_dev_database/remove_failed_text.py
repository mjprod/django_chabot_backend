# remove the text that isnt needed

input_file = "translated_member_messages_en_2.txt"
output_file = "en_cleaned_2.txt"


def remove_failed_text(input_file, output_file):
    exclude_patterns = [
        "pa =",
        "[Translation failed for line =]",
        "[Translation failed for line .]",
        "hi",
        "done",
        "sorry",
        "=" "yes",
        "ok",
    ]

    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", encoding="utf-8"
    ) as outfile:
        for line in infile:
            if not any(pattern in line.lower() for pattern in exclude_patterns):
                outfile.write(line)


remove_failed_text(input_file, output_file)
print("process complete. result saved in", output_file)
