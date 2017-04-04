import sqlite3


def create_db(db_name):
    """create db"""
    sql_fk = "PRAGMA foreign_keys = ON ;"
    
    sql_create_user = """ CREATE TABLE IF NOT EXISTS  user(
    id_             INTEGER     PRIMARY KEY AUTOINCREMENT NOT NULL,
    name            TEXT (120)  NOT NULL,
    surname         TEXT(120)   ,
    age             INTEGER 
    );
    """

    sql_create_thing_type = """CREATE TABLE IF NOT EXISTS  thing_type(
    id_             INTEGER     PRIMARY KEY AUTOINCREMENT NOT NULL,
    name            TEXT(50)    NOT NULL
    );
    """

    sql_create_thing = """CREATE TABLE IF NOT EXISTS  thing(
    id_             INTEGER      PRIMARY KEY AUTOINCREMENT NOT NULL,
    date_           TEXT(23)     NOT NULL,
    name            TEXT(50)     NOT NULL,
    additional_info TEXT(500)    ,
    sum_            INTEGER      NOT NULL,
    user            INTEGER      NOT NULL,
    thing_type      INTEGER      NOT NULL,
    cost_remain     INTEGER      NOT NULL,
    pay_count       INTEGER      NOT NULL,
    shipment        INTEGER      NOT NULL,
    FOREIGN KEY (shipment)   REFERENCES   shipment(id_) ON DELETE RESTRICT,
    FOREIGN KEY (user)       REFERENCES   user(id_) ON DELETE RESTRICT,
    FOREIGN KEY (thing_type) REFERENCES   thing_type(id_) ON DELETE RESTRICT
    );
    """

    sql_create_pay = """ CREATE TABLE IF NOT EXISTS  pay(
    id_             INTEGER     PRIMARY KEY AUTOINCREMENT NOT NULL,
    sum_            INTEGER     NOT NULL,
    date_           INTEGER(8)  NOT NULL,
    caption         TEXT(50)    NOT NULL,
    user            INTEGER     NOT NULL,
    thing           INTEGER     NOT NULL,
    FOREIGN KEY (user)      REFERENCES user(id_)     ON DELETE RESTRICT, 
    FOREIGN KEY (thing)     REFERENCES thing(id_)    ON DELETE RESTRICT
    );
    """

    sql_create_shipment = """CREATE TABLE IF NOT EXISTS shipment(
        id_     INTEGER PRIMARY KEY AUTOINCREMENT,
        sum_    INTEGER NOT NULL,
        date_   INTEGER(8) NOT NULL,
        name    TEXT(50) NOT NULL
        );
        """

    sql_create_shipment_pay = """CREATE TABLE IF NOT EXISTS shipment_pay(
        id_     INTEGER PRIMARY KEY AUTOINCREMENT,
        sum_    INTEGER NOT NULL,
        date_   INTEGER(8) NOT NULL,
        shipment INTEGER NOT NULL,
        FOREIGN KEY (shipment) REFERENCES shipment(id_) ON DELETE RESTRICT
        );
    """

    cmd_list = (sql_fk, sql_create_user, sql_create_thing_type,
                sql_create_pay, sql_create_shipment,
                sql_create_shipment_pay, sql_create_thing
                )
    try:
        conn = sqlite3.connect(db_name)
    except sqlite3.Error as e:
        print "Connection error: ", e.args[0]
    else:
        for cmd in cmd_list:
            try:
                conn.execute(cmd)
                
            except sqlite3.Error as e:
                print "SQL execute error: ", e.args[0]
                print cmd
                break
        conn.commit()
        conn.close()
