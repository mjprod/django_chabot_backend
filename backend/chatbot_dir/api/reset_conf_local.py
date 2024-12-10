import json
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def reset_all_confidence_scores(target_score=0.5):
    try:
        logger.info(f"Starting bulk confidence score update to {target_score}")
        base_dir = os.path.join(Path(__file__).parent.parent, "data")
        database_files = [
            "database_part_1.json",
            "database_part_2.json",
            "database_part_3.json",
        ]

        total_updates = 0
        for database_file in database_files:
            file_path = os.path.join(base_dir, database_file)
            try:
                with open(file_path, "r+") as f:
                    # Load the outer array
                    data = json.load(f)
                    updates_made = 0

                    # Access the inner array (first element)
                    if data and isinstance(data[0], list):
                        inner_array = data[0]

                        # Update confidence scores
                        for item in inner_array:
                            if isinstance(item, dict) and "metadata" in item:
                                current_confidence = item["metadata"].get(
                                    "confidence", 0
                                )
                                item["metadata"]["confidence"] = target_score
                                updates_made += 1

                        # Update the data structure
                        data[0] = inner_array

                    if updates_made > 0:
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()

                    total_updates += updates_made
                    logger.info(
                        f"Updated {updates_made} confidence scores in {database_file}"
                    )

            except FileNotFoundError:
                logger.error(f"Database file not found: {database_file}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in file: {database_file}")
            except Exception as e:
                logger.error(f"Error processing file {database_file}: {str(e)}")

        logger.info(f"Completed confidence score reset. Total updates: {total_updates}")

    except Exception as e:
        logger.error(f"Error in bulk confidence update: {str(e)}")


if __name__ == "__main__":
    reset_all_confidence_scores(0.5)
