# imports
import json
import os


# create json clean function
def clean_json_data(file_path):
    valid_inputs = {
        "user_input": str,
        "ai_response": str,
        "correct_bool": bool,
        "chat_rating": int,
        "incorrect_answer_response": str,
        "metadata": dict,
    }

    # this is a check to see if the file path and json file exists
    # for when we clean data and update to the current database to start again
    if not os.path.exists(file_path):
        print("file/s not found!")
        return
    # open the json and read file
    with open(file_path, "r") as f:
        try:
            interactions = json.load(f)
        except json.JSONDecodeError:
            print("Error with json decode!")
            return
    # clean data loop
    cleaned_data = []
    for ii in interactions:
        cleaned_interaction = {}
        for key, expected_type in valid_inputs.items():
            value = ii.get(key, None)
            if isinstance(value, expected_type):
                cleaned_interaction[key] = value if value != "" else None
            else:
                cleaned_interaction[key] = (
                    None  # this will replace any invalid types with None
                )
        cleaned_data.append(cleaned_interaction)

    # this will write the cleaned data back into the JSON File
    with open(file_path, "w") as f:
        json.dump(cleaned_data, f, indent=4)

    print("data has been cleaned!")


# load our file as file_path
file_path = os.path.join(os.path.dirname(__file__), "../data/interactions.json")
clean_json_data(file_path)
