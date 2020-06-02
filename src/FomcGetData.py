from datetime import date
import numpy as np
import pandas as pd
import pickle
import sys
from fomc_get_data.FomcStatement import FomcStatement
from fomc_get_data.FomcMinutes import FomcMinutes
from fomc_get_data.FomcMeetingScript import FomcMeetingScript
from fomc_get_data.FomcPresConfScript import FomcPresConfScript
from fomc_get_data.FomcSpeech import FomcSpeech

def download_data(fomc, from_year=1990):
    fomc.get_contents(from_year)
    fomc.pickle_dump_df(filename = fomc.content_type + ".pickle")
    fomc.save_texts(prefix = fomc.content_type + "/FOMC_" + fomc.content_type + "_")

if __name__ == '__main__':
    pg_name = sys.argv[0]
    args = sys.argv[1:]
    content_type_all = ('statement', 'minutes', 'meeting_script', 'presconf_script', 'speech', 'all')
    
    if len(sys.argv) != 2:
        print("Usage: ", pg_name)
        print("Please specify ONE argument from ", content_type_all)
        sys.exit(1)

    content_type = args[0].lower()
    if content_type not in content_type_all:
        print("Usage: ", pg_name)
        print("Please specify ONE argument from ", content_type_all)
        sys.exit(1)

    if content_type == 'all':
        fomc = FomcStatement()
        download_data(fomc)
        fomc = FomcMinutes()
        download_data(fomc)
        fomc = FomcMeetingScript()
        download_data(fomc)
        fomc = FomcPresConfScript()
        download_data(fomc)
        fomc = FomcSpeech()
        download_data(fomc)
    else:
        if content_type == 'statement':
            fomc = FomcStatement()
        elif content_type == 'minutes':
            fomc = FomcMinutes()
        elif content_type == 'meeting_script':
            fomc = FomcMeetingScript()
        elif content_type == 'presconf_script':
            fomc = FomcPresConfScript()
        elif content_type == 'speech':
            fomc = FomcSpeech()

        download_data(fomc)

