from pathlib import Path
import conffwk
import sys
import os
from logging import getLogger
log = getLogger('daqconf.consolidate')


def get_all_includes(db, file):
    includes = db.get_includes(file)
    for include in includes:
        if "data.xml" not in include:
            continue
        includes += get_all_includes(db, include)

    return list(set(includes))

def consolidate_db(oksfile, output_file):
    log.info(f"Consolidating database into output database \'{output_file}\'. Input database: \'{oksfile}\'.")

    sys.setrecursionlimit(10000)  # for example
    log.debug("Reading database")
    db = conffwk.Configuration("oksconflibs:" + oksfile)

    schemafiles = []
    includes = get_all_includes(db, None)
    schemafiles += [i for i in includes if "schema.xml" in i]
    log.debug(f"Included schemas: {schemafiles}")

    log.debug("Creating new database")
    new_db = conffwk.Configuration("oksconflibs")
    new_db.create_db(output_file, schemafiles)

    new_db.commit()

    log.debug("Reading dal objects from old db")
    dals = db.get_all_dals()

    log.debug(f"Copying objects to new db")

    for dal in dals:
        this_dal = db.get_dal(dals[dal].className(), dals[dal].id)
        new_db.add_dal(this_dal)

    log.debug("Saving database")
    new_db.commit()


def copy_configuration(dest_dir : Path, input_files: list):
    if len(input_files) == 0:
        return []

    log.info(f"Copying configuration represented by databases: \'{input_files}\' to \'{dest_dir}\'")
    dest_dir = dest_dir.resolve() # Always include by absolute path when copying
    sys.setrecursionlimit(10000)  # for example

    output_dbs = []

    for input_file in input_files:
        db = conffwk.Configuration("oksconflibs:" + input_file)
        includes = db.get_includes(None)
        schemas = [i for i in includes if "schema.xml" in i]
        dbs = [i for i in includes if "data.xml" in i]
        newdbs = copy_configuration(dest_dir, dbs)

        output_file = dest_dir / os.path.basename(input_file)

        new_db = conffwk.Configuration("oksconflibs")
        new_db.create_db(str(output_file), schemas + newdbs)
        new_db.commit()

        dals = db.get_all_dals()

        for dal in dals:

            db.get_dal(dals[dal].className(), dals[dal].id)

            new_db.add_dal(dals[dal])

        new_db.commit()
        output_dbs.append(str(output_file))
    log.debug("DONE")

    return output_dbs


def consolidate_files(oksfile, *input_files):
    includes = []
    dbs = []
    str_in_files = '\n'.join(input_files)
    log.info(f"Consolidating {len(input_files)} databases into output database \'{oksfile}\'. Input databases: {str_in_files}")
    sys.setrecursionlimit(10000)  # for example

    for input_file in input_files:
        dbs.append(conffwk.Configuration("oksconflibs:" + input_file))
        includes += get_all_includes(dbs[len(dbs) - 1], None)

    includes = list(set(includes))
    includes = [i for i in includes if i not in input_files]
    log.debug(f"Included files: {includes}")

    new_db = conffwk.Configuration("oksconflibs")
    new_db.create_db(oksfile, includes)

    new_db.commit()

    for db in dbs:
        log.debug(f"Reading dal objects from old db {db}")
        dals = db.get_all_dals()

        log.debug(f"Copying objects to new db {new_db}")
        for dal in dals:

            try:
                new_db.get_dal(dals[dal].className(), dals[dal].id)
            except:
                new_db.add_dal(dals[dal])
            new_db.commit()

    log.debug(f"Saving database {new_db}")
    new_db.commit()