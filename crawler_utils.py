import json
import os.path

def save_submission(submission, storage_dir):
    with open(os.path.join(storage_dir, submission.id), "w") as f:
        f.write(json.dumps({"url": submission.permalink,
                            "text": submission.selftext, 
                            "title" : submission.title}))
        f.close()

