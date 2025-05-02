from pprint import pprint

import dlwheel

cfg = dlwheel.setup()
pprint(cfg.to_dict())
