FORMAT_OPTIONS = {
    1: "%(levelname)s | %(asctime)s | %(module)s | %(message)s | %(context)s",
    2: "%(levelname)s | %(asctime)s | %(context)s | %(message)s | %(exc_text)s",
    3: "%(levelname)s | %(context)s | %(message)s | %(stack_info)s",
    4: "%(context)s | %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    5: "%(levelname)s | %(message)s | %(context)s | [in %(pathname)s:%(lineno)d]",
    6: "%(asctime)s | %(context)s | %(levelname)s | %(message)s | %(exc_info)s",
    7: "%(levelname)s | %(asctime)s | %(context)s | in %(module)s: %(message)s",
    8: "%(levelname)s | %(context)s | %(message)s | [%(filename)s:%(lineno)d]",
    9: "[%(asctime)s] | %(levelname)s | %(context)s | in %(module)s: %(message)s",
    10: "%(asctime)s | %(processName)s | %(context)s | %(name)s | %(levelname)s | %(message)s",
    11: "%(asctime)s | %(context)s | %(threadName)s | %(name)s | %(levelname)s | %(message)s",
    12: "%(levelname)s | [%(asctime)s] | %(context)s | (%(filename)s:%(lineno)d) | %(message)s",
    13: "%(levelname)s | [%(asctime)s] | %(context)s | {%(name)s} | (%(filename)s:%(lineno)d): %(message)s",
    14: "[%(asctime)s] | %(levelname)s | %(context)s | %(name)s | %(module)s | %(message)s",
    15: "%(levelname)s | %(context)s | %(asctime)s | %(filename)s:%(lineno)d | %(message)s",
    16: "%(levelname)s | %(context)s | %(message)s | [%(asctime)s] | %(module)s",
    17: "%(levelname)s | %(context)s | [%(asctime)s] | %(process)d | %(message)s",
    18: "%(levelname)s | %(context)s | %(asctime)s | %(name)s | %(message)s",
    19: "%(levelname)s | %(asctime)s | %(context)s | %(module)s:%(lineno)d | %(message)s",
    20: "[%(asctime)s] | %(levelname)s | %(context)s | %(thread)d | %(message)s",
}
