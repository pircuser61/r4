# -*- coding: utf-8 -*-

import os
import sqlite3

from createBase import create_db

dbFile = os.path.join(os.path.dirname(__file__), 'db', 'x')


class DbItem(object):
    def __init__(self, connection):
        self._conn = connection
        self.messages = []

    def _execute(self, sql, *param):
        try:
            if param:
                self._conn.execute(sql, param)
            else:
                self._conn.execute(sql)
            self._conn.commit()
        except sqlite3.Error as e:
            self.msg(str(e))

    def _execute_no_commit(self, sql, *param):
        try:
            if param:
                self._conn.execute(sql, param)
            else:
                self._conn.execute(sql)
        except sqlite3.Error as e:
            self.msg(str(e))
        else:
            return True

    def _get_one(self, sql, *param):
        try:
            if param:
                return self._conn.execute(sql, param).fetchone()
            else:
                return self._conn.execute(sql).fetchone()
        except sqlite3.Error as e:
            self.msg(str(e))

    def _get_all(self, sql, *param):
        try:
            if param:
                return self._conn.execute(sql, param).fetchall()
            else:
                return self._conn.execute(sql).fetchall()
        except sqlite3.Error as e:
            self.msg(str(e))

    def get_messages(self):
        tmp = self.messages
        self.messages = []
        return tmp

    def get_message_str(self):
        return ", ".join(self.get_messages())

    def msg(self, text):
        self.messages.append(text)


class DB(object):

    def __init__(self):
        self.lastErr = ""

        try:
            self._conn = sqlite3.connect(dbFile)
            self._conn.execute("PRAGMA foreign_keys = ON ;")

            self.type = ThingType(self._conn)
            self.thing = Thing(self._conn)
            self.pay = Pay(self._conn)
            self.user = User(self._conn)
            self.shipment = Shipment(self._conn)
            self.shipment_pay = ShipmentPay(self._conn)
        except sqlite3.Error as e:
            self.lastErr = str(e)

    def shipment_pay_add(self, sum_, date, shipment):
        obj = self.shipment_pay
        if obj.add_no_commit(sum_, date, shipment):
            paid = obj.paid(shipment)
            cost = self.shipment.sum(shipment)
            if paid is not None and cost is not None:
                if cost >= paid:
                    self._conn.commit()
                    obj.msg("done")
                    return
                obj.msg("pay > sum remain")
            else:
                obj.msg(u"ошибка получения данных")
        else:
            obj.msg("sql error")
        self._conn.rollback()

    def pay_add(self, date, caption, user, thing, sum_):
        obj = self.pay
        if obj.add_no_commit(date, caption, user, thing, sum_):
            thing_sum = self.thing.sum(thing)
            pay_sum = obj.sum_by_thing(thing)
            if thing_sum is not None and pay_sum is not None:
                if thing_sum >= pay_sum:
                    self._conn.commit()
                    obj.msg("done")
                    return
                else:
                    obj.msg("SUM(pay.sum) > thing.sum")
            else:
                obj.msg(u"ошибка получения данных")
        else:
            obj.msg("sql error")
        self._conn.rollback()

    def thing_add(self, name, thing_type, user, shipment, date, sum_, info):
        obj = self.thing
        if obj.add_no_commit(name, thing_type, user, shipment, date, sum_, info):
            shipment_sum = self.shipment.sum(shipment)
            thing_sum = obj.sum_by_shipment(shipment)
            if shipment_sum is not None and thing_sum is not None:
                if shipment_sum >= thing_sum:
                    self._conn.commit()
                    obj.msg("done")
                    return
                else:
                    obj.msg("SUM(thing.sum) > shipment.sum")
            else:
                obj.msg(u"ошибка получения данных")
        else:
            obj.msg("sql error")
        self._conn.rollback()

    def shipment_pay_upd(self, id_, sum_, date, shipment):
        obj = self.shipment_pay
        if obj.upd_no_commit(id_, sum_, date, shipment):
            paid = obj.paid(shipment)
            cost = self.shipment.sum(shipment)
            if cost >= paid:
                self._conn.commit()
                obj.msg("done")
                return
            obj.msg("pay > sum remain")
        self._conn.rollback()

    def pay_upd(self, id_, date, caption, user, thing, sum_):
        obj = self.pay
        thing_sum = self.thing.sum(thing)
        pay_sum = obj.sum_by_thing(thing)
        if thing_sum is not None and pay_sum is not None:
            if thing_sum >= pay_sum + int(sum_):
                obj.update(id_, date, caption, user, thing, sum_)
            else:
                obj.msg("SUM(pay.sum) > thing.sum")
        else:
            obj.msg(u"ошибка получения данных")


class User (DbItem):
    sql_add = "INSERT INTO user (name, surname, age) VALUES (?,?,?)"
    sql_upd = "UPDATE user SET name = ?, surname= ?,  age= ? WHERE id_ = ?"
    sql_del = "DELETE FROM user WHERE id_ = ?"
    sql_get = "SELECT id_, name, surname, age FROM user WHERE id_ = ?"
    sql_list = "SELECT id_, name, surname, age FROM user"
    sql_listNames = "SELECT id_, name FROM user"
    sql_listLimit = """ SELECT a.id_, a.name, a.surname, a.age
                        FROM (SELECT id_ FROM user LIMIT ?,10) as b
                        JOIN user as a
                        ON b.id_ = a.id_ """
    sql_top_spend_on_other = """ SELECT filter.user, user.name, filter.paid
                        FROM (SELECT pay.user, SUM(pay.sum_) AS paid
                                FROM pay
                                LEFT JOIN thing ON pay.thing = thing.id_
                                WHERE pay.user <> thing.user
                                GROUP BY pay.user ORDER BY paid DESC
                                LIMIT 10) AS filter
                        LEFT JOIN user
                        ON user.id_ = filter.user
                       """
    sql_cadger = """ SELECT filter.user, user.name, filter.total_cost
                        FROM (SELECT user, SUM(sum_) AS total_cost
                                FROM thing
                                GROUP BY user ORDER BY total_cost DESC
                                LIMIT 10) AS filter
                        LEFT JOIN user
                        ON user.id_ = filter.user
                       """
    sql_top_spend = """ SELECT filter.user, user.name, filter.paid
                        FROM (SELECT user, SUM(pay.sum_) AS paid
                            FROM pay
                            GROUP BY user ORDER BY paid DESC
                            LIMIT 10) AS filter
                        LEFT JOIN user
                        ON user.id_ = filter.user
                       """
    sql_top_spend_1 = """SELECT user.id_, user.name, SUM(pay.sum_) as paid
                        FROM pay, user
                        WHERE user.id_ = pay.user
                        GROUP BY user ORDER BY paid DESC
                        LIMIT 10
                       """
    sql_count = "SELECT COUNT (id_) FROM user"

    def _check_params(self, name, surname, age):
        ok = True
        if not name:
            self.msg(u"Имя не может быть пустым")
            ok = False
        if not age:
            self.msg(u"Возраст не может быть пустым")
            ok = False
        else:
            try:
                int(age)
            except ValueError:
                ok = False
                self.msg(u"Возраст должен быть целым числом")
        return ok

    def add(self, name, surname, age):
        if self._check_params(name, surname, age):
            self._execute(self.sql_add, name, surname, age)

    def add_no_commit(self, name, surname, age):
        if self._check_params(name, surname, age):
            self._execute_no_commit(self.sql_add, name, surname, age)

    def update(self, id_, name, surname, age):
        if self._check_params(name, surname, age):
            self._execute(self.sql_upd, name, surname, age, id_)

    def get_list(self, start=None):
        if start is None:
            return self._get_all(self.sql_list)
        else:
            return self._get_all(self.sql_listLimit, start)

    def get_list_names(self):
        return self._get_all(self.sql_listNames)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def delete(self, id_):
        self._execute(self.sql_del, id_)

    def count(self):
        res = self._get_one(self.sql_count)
        if res:
            return res[0]
        else:
            return 0

    def get_top_spend_on_other(self):
        return self._get_all(self.sql_top_spend_on_other)

    def get_top_spend(self):
        return self._get_all(self.sql_top_spend)

    def get_top_spend_1(self):
        return self._get_all(self.sql_top_spend_1)

    def get_cadger(self):
        return self._get_all(self.sql_cadger)


class ThingType(DbItem):
    sql_add = "INSERT INTO thing_type (name) VALUES (?)"
    sql_upd = "UPDATE thing_type SET name = ? WHERE id_ = ?"
    sql_del = "DELETE FROM thing_type WHERE id_ = ?"
    sql_get = "SELECT * FROM thing_type WHERE id_ = ?"
    sql_list = "SELECT * FROM thing_type"
    sql_count = "SELECT COUNT (id_) FROM thing_type"

    def _check_params(self, name):
        if name:
            return True
        else:
            self.msg("Имя не может быть пустым")

    def count(self):
        return self._get_one(self.sql_count)[0]

    def add(self, name):
        if self._check_params(name):
            self._execute(self.sql_add, name)

    def add_no_commit(self, name):
        if self._check_params(name):
            self._execute_no_commit(self.sql_add, name)

    def delete(self, id_):
        self._execute(self.sql_del, id_)

    def update(self, id_, name):
        if self._check_params(name):
            self._execute(self.sql_upd, name, id_)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def get_list(self):
        return self._get_all(self.sql_list)


class Thing(DbItem):
    sql_add = """INSERT INTO thing
               (name,thing_type,user,shipment, date_, sum_, additional_info,
                cost_remain, pay_count)
                VALUES (?,?,?,?,?,?,?,?,0)"""
    sql_upd = """UPDATE thing SET
                 name = ?, thing_type = ?, user = ?, shipment = ?,
                 date_ = ?, sum_ = ?, cost_remain = ?, additional_info = ?
                 WHERE id_ = ?"""
    sql_del = """DELETE FROM  thing WHERE id_ = ?"""
    sql_get = """SELECT
                 id_, name, thing_type, user, shipment, date_, sum_, additional_info
                 FROM thing WHERE id_ = ? """
    sql_list_names = """SELECT id_, name, cost_remain, pay_count FROM thing"""
    sql_list_old = """SELECT
                        thing.id_, thing.name,
                        thing_type.name, user.name, shipment.name,
                        datetime(thing.date_, 'unixepoch', 'localtime'),
                        thing.sum_, thing.cost_remain, thing.pay_count
                        FROM thing
                        LEFT JOIN user ON thing.user = user.id_
                        LEFT JOIN thing_type ON thing.thing_type = thing_type.id_
                        LEFT JOIN shipment ON thing.shipment = shipment.id_
                     """
    sql_list = """SELECT
                        thing.id_, thing.name,
                        thing_type.name, user.name, shipment.name,
                        datetime(thing.date_, 'unixepoch', 'localtime'),
                        thing.sum_, tp.s, tp.c
                        FROM thing
                        LEFT JOIN user ON thing.user = user.id_
                        LEFT JOIN thing_type ON thing.thing_type = thing_type.id_
                        LEFT JOIN shipment ON thing.shipment = shipment.id_
                        LEFT JOIN (SELECT thing, SUM (sum_) AS s, COUNT(sum_) AS c
                                    FROM pay GROUP BY thing) AS tp
                                    ON thing.id_ = tp.thing


                     """
    sql_list_paid = """SELECT
                        thing.id_, thing.name,
                        thing.thing_type, thing.user, thing.shipment,
                        datetime(thing.date_, 'unixepoch', 'localtime'),
                        thing.sum_, tp.s, tp.c
                        FROM thing
                        LEFT JOIN (SELECT thing, SUM (sum_) AS s, COUNT (sum_) AS c
                               FROM pay GROUP BY thing) AS tp
                         ON thing.id_ = tp.thing
                         WHERE thing.sum_ = tp.s
                     """
    sql_list_unpaid = """SELECT
                        thing.id_, thing.name,
                        thing.thing_type, thing.user, thing.shipment,
                        datetime(thing.date_, 'unixepoch', 'localtime'),
                        thing.sum_, tp.s, tp.c
                        FROM thing
                        LEFT JOIN (SELECT thing, SUM (sum_) AS s, COUNT (sum_) AS c
                               FROM pay GROUP BY thing) AS tp
                         ON thing.id_ = tp.thing
                         WHERE thing.sum_ <> tp.s OR tp.s IS NULL
                     """
    sql_list_total = """
                        SELECT sh.id_, sh.name, sh.sum_, sh.paid,
                                th.count, th.sum, th.paid
                        FROM
                            (SELECT shipment.id_, shipment.name, shipment.sum_,
                             sp.paid AS paid
                             FROM shipment
                             LEFT JOIN
                                (SELECT shipment, SUM(sum_) as paid
                                 FROM shipment_pay GROUP BY shipment
                                 ) AS sp
                                ON shipment.id_ = sp.shipment
                            ) AS sh


                        LEFT OUTER JOIN
                            (SELECT COUNT (thing.id_) as count,
                                    SUM(thing.sum_) as sum,
                                    SUM(tp.paid) as paid,
                                    thing.shipment
                             FROM thing
                             LEFT JOIN
                                 (SELECT thing, SUM (sum_) AS paid
                                  FROM pay
                                  GROUP BY thing
                                  ) AS tp
                                ON thing.id_ = tp.thing

                             GROUP BY thing.shipment
                             ) AS th
                         ON sh.id_ = th.shipment
                         GROUP BY sh.id_
                     """
    sql_list_full_paid = """
                        SELECT sh.id_, sh.name, sh.sum_, sh.paid,
                                th.count, th.sum, th.paid
                        FROM
                            (SELECT shipment.id_, shipment.name, shipment.sum_,
                             sp.paid AS paid
                             FROM shipment
                             LEFT JOIN
                                (SELECT shipment, SUM(sum_) as paid
                                 FROM shipment_pay GROUP BY shipment
                                 ) AS sp
                                ON shipment.id_ = sp.shipment
                             WHERE sp.paid = shipment.sum_
                            ) AS sh


                        JOIN
                            (SELECT COUNT (thing.id_) as count,
                                    SUM(thing.sum_) as sum,
                                    SUM(tp.paid) as paid,
                                    thing.shipment
                             FROM thing
                             LEFT JOIN
                                 (SELECT thing, SUM (sum_) AS paid
                                  FROM pay
                                  GROUP BY thing
                                  ) AS tp
                                ON thing.id_ = tp.thing
                             WHERE thing.sum_ = tp.paid
                             GROUP BY thing.shipment
                             ) AS th
                         ON sh.id_ = th.shipment
                         GROUP BY sh.id_
                     """

    sql_list_limit = """SELECT
                        thing.id_, thing.name,
                        thing_type.name, user.name, shipment.name,
                        datetime(thing.date_, 'unixepoch', 'localtime'),
                        thing.sum_, thing.cost_remain, thing.pay_count
                        FROM
                        (SELECT id_ FROM thing LIMIT ?,10) as filter
                        LEFT JOIN thing ON filter.id_ = thing.id_
                        LEFT JOIN user ON thing.user = user.id_
                        LEFT JOIN thing_type ON thing.thing_type = thing_type.id_
                        LEFT JOIN shipment ON thing.shipment = shipment.id_
                     """
    sql_unpaid = """SELECT thing.id_, thing.name,
                        thing_type.name,
                        user.name, thing.shipment,
                        thing.sum_, thing.cost_remain, thing.pay_count
                    FROM thing
                    JOIN (SELECT id_ FROM thing WHERE  thing.cost_remain > 0) AS filter
                        ON filter.id_ = thing.id_
                    LEFT JOIN user ON user.id_ = thing.user
                    LEFT JOIN thing_type ON thing_type.id_ = thing.thing_type
                    """
    sql_unpaid_id = """SELECT thing.id_, thing.cost_remain, thing.pay_count
                       FROM thing WHERE  thing.cost_remain > 0"""
    sql_count = """SELECT COUNT(id_) FROM thing"""
    sql_sum_remain = """SELECT cost_remain FROM thing WHERE id_ = ?"""
    sql_sum = "SELECT sum_ FROM thing WHERE id_ = ?"
    sql_set_remain = """UPDATE thing SET  cost_remain = ? WHERE id_ = ? """
    sql_shipment_sum = "SELECT SUM (sum_) FROM thing WHERE shipment = ?"

    def _check_params(self, name, thing_type, user, date, sum_, additional_info):
        ok = True

        if not name:
            ok = False
            self.msg(u"Имя не может быть пустым")
        if not thing_type:
            ok = False
            self.msg(u"Не выбран тип")
        if not user:
            ok = False
            self.msg(u"Не выбран user")

        if not sum_:
            ok = False
            self.msg("empty sum")
        else:
            try:
                if int(sum_) <= 0:
                    ok = False
                    self.msg("sum less or equal 0")
            except ValueError:
                ok = False
                self.msg("sum not a number")
        return ok

    def add(self, name, thing_type, user, shipment, date, sum_, additional_info=""):
        if self._check_params(name, thing_type, user, date, sum_, additional_info):
            self._execute(self.sql_add, name, thing_type, user, shipment,
                          date, sum_, additional_info, sum_
                          )

    def update(self, id_, name, thing_type, user, shipment, date, sum_, remain,  additional_info):
        """id_, name, thing_type, user, shipment, date, sum_, additional_info"""
        if self._check_params(name, thing_type, user, date, sum_, additional_info):
            return self._execute(
                self.sql_upd, name, thing_type, user, shipment, date,
                sum_, remain, additional_info, id_
                )

    def delete(self, id_):
        self._execute(self.sql_del, id_)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def get_unpaid(self):
        return self._get_all(self.sql_unpaid)

    def get_list(self, start):
        return self._get_all(self.sql_list)

    def list_paid(self):
        return self._get_all(self.sql_list_paid)

    def list_unpaid(self):
        return self._get_all(self.sql_list_unpaid)

    def list_full_paid(self):
        return self._get_all(self.sql_list_full_paid)

    def list_total(self):
        return self._get_all(self.sql_list_total)

    def get_list_names(self):
        return self._get_all(self.sql_list_names)

    def count(self):
        res = self._get_one(self.sql_count)
        if res:
            return res[0]
        else:
            return 0

    def sum(self, id_):
        # проверка res на случай ошибки выполнения запроса (res - null)
        # проверка res[0] на случай если thing не найден (res -() )
        res = self._get_one(self.sql_sum, id_)
        if res and res[0]:
            return int(res[0])

    def sum_remain(self, id_):
        return self._get_one(self.sql_sum_remain, id_)

    def set_remain(self, id_, remain):
        return self._execute_no_commit(self.sql_set_remain, remain, id_)

    def sum_by_shipment(self, shipment):
        # проверка res на случай ошибки выполнения запроса (res - null)
        res = self._get_one(self.sql_shipment_sum, shipment)
        if res:
            return int(res[0])

    def add_no_commit(self, name, thing_type, user, shipment, date, sum_, additional_info=""):
        if self._check_params(name, thing_type, user, date, sum_, additional_info):
            return self._execute_no_commit(
                self.sql_add, name, thing_type, user, shipment,
                date, sum_, additional_info, sum_
                )

    # методы для генератора
    def get_unpaid_id(self):
        return self._get_all(self.sql_unpaid_id)

    # def _check_cost(self, id_):
    #    sum_ = int(self._get_one(self.sql_get, id_)[6])
    #    paid = int(self._paid(id_))
    #    return sum_ >= paid


class Pay(DbItem):
    """pay: id_, date_, caption, user,  thing, sum_"""

    sql_add = """INSERT INTO pay (date_, caption, user,  thing, sum_)
            VALUES (?, ?, ?, ?, ?)"""
    sql_upd = """UPDATE pay SET date_ = ?, caption = ?, user = ?,
            thing =?, sum_ = ? WHERE id_ = ?"""
    sql_del = """DELETE FROM pay WHERE id_ =  ?"""
    sql_get = """SELECT id_, date_, caption, user, thing, sum_
            FROM pay WHERE id_ = ?"""
    sql_list = """SELECT
            pay.id_,
            datetime(pay.date_,'unixepoch','localtime'),
            pay.caption, user.name, thing.name, pay.sum_
            FROM pay
            LEFT JOIN user ON pay.user = user.id_ 
            LEFT JOIN thing ON pay.thing = thing.id_"""

    sql_filtered = """SELECT pay.id_,
            datetime(pay.date_,'unixepoch','localtime'),
            pay.caption, u.name, t.name, t.id_, pay.sum_
            FROM pay
            """
    sql_filtered_date = """JOIN (SELECT id_ FROM pay WHERE date_ BETWEEN ? AND ?)
                            as time_filter
                            ON pay.id_ = time_filter.id_ """
    sql_filter_user_ON = """JOIN (SELECT id_, name FROM user WHERE name LIKE ?) AS u
                            ON pay.user = u.id_ """
    sql_filter_user_OFF = "LEFT JOIN user AS u ON pay.user = u.id_ "
    sql_filter_thing_ON = """JOIN (SELECT id_, name FROM thing WHERE thing.name LIKE ?) AS t
                             ON pay.thing = t.id_ """
    sql_filter_thing_OFF = "LEFT JOIN thing AS t ON pay.thing = t.id_ "
    sql_filter_start = "LIMIT ?,10"

    sql_sum_and_thing = "SELECT sum_, thing FROM pay WHERE id_ = ?"
    sql_sum_by_thing = "SELECT SUM(sum_) FROM pay WHERE  thing = ?"
    sql_group_by_days = """SELECT (date_ - ?) / 86400, COUNT(id_) FROM pay
                           WHERE date_ BETWEEN ? AND ?
                           GROUP BY (date_ - ?) / 86400
                           ORDER BY date_"""
    sql_count = """SELECT COUNT (id_) FROM pay"""

    def _check_params(self, date_, caption, user, thing, sum_):
        ok = True
        if not date_:
            ok = False
            self.msg("empty date")
        if not user:
            ok = False
            self.msg("empty user")
        if not thing:
            ok = False
            self.msg("empty thing")
        if not sum_:
            ok = False
            self.msg("empty sum")
        else:
            try:
                if int(sum_) <= 0:
                    ok = False
                    self.msg("sum less or equal 0")
            except ValueError:
                ok = False
                self.msg("sum not a number")
        return ok

    def add_no_commit(self, date_, caption, user, thing, sum_):
        """date_, caption, user, thing, sum_"""
        if self._check_params(date_, caption, user, thing, sum_):
            return self._execute_no_commit(self.sql_add, date_, caption, user, thing, sum_)

    def add(self, date_, caption, user, thing, sum_):
        """date_, caption, user, thing, sum_"""
        if self._check_params(date_, caption, user, thing, sum_):
            return self._execute(self.sql_add, date_, caption, user, thing, sum_)

    def delete(self, id_):
        return self._execute(self.sql_del, id_)

    def update_no_commit(self, id_, date_, caption, user, thing, sum_):
        if self._check_params(date_, caption, user, thing, sum_):
            return self._execute_no_commit(self.sql_upd, date_, caption, user, thing, sum_, id_)

    def update(self, id_, date_, caption, user, thing, sum_):
        if self._check_params(date_, caption, user, thing, sum_):
            return self._execute(self.sql_upd, date_, caption, user, thing, sum_, id_)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def get_list(self):
        return self._get_all(self.sql_list)

    def get_filtered_list(self, start, user, thing, begin, end):
        """params[0] - page, [1] - user_filter, [2] - thing filter"""

        params = []

        sql = self.sql_filtered
        if begin and end:
            sql += self.sql_filtered_date
            params.append(begin)
            params.append(end)

        if user:
            sql += self.sql_filter_user_ON
            params.append(user+'%')
        else:
            sql += self.sql_filter_user_OFF

        if thing:
            sql += self.sql_filter_thing_ON
            params.append(thing+'%')
        else:
            sql += self.sql_filter_thing_OFF
        if start:
            sql += self.sql_filter_start
            params.append(start)

        #
        # user_filter = self.sql_filter_user_ON if kwargs["user"] else self.sql_filter_user_OFF
        # thing_filter = self.sql_filter_thing_ON if kwargs["thing"] else self.sql_filter_thing_OFF
        return self._get_all(sql, *params)

    def count(self):
        return self._get_one(self.sql_count)[0]

    def sum_n_thing(self, id_):
        return self._get_one(self.sql_sum_and_thing, id_)

    def sum_by_thing(self, thing):
        res = self._get_one(self.sql_sum_by_thing, thing)
        return int(res[0]) if res[0] else 0

# for generator
    def group_by_date(self, begin, end):
        return self._get_all(self.sql_group_by_days, begin, begin, end, begin)


class Shipment(DbItem):
    sql_add = """INSERT INTO shipment (name, sum_, date_) VALUES (?,?,?)"""
    sql_upd = """UPDATE shipment SET sum_ = ?, date_ = ?, name = ? WHERE id_ = ?"""
    sql_del = """ DELETE FROM shipment WHERE id_ = ?"""
    sql_get = """SELECT id_, name, sum_, date_ FROM shipment WHERE id_ = ?"""
    sql_list = """SELECT id_, name, sum_, datetime(date_,'unixepoch','localtime'),
                   sp.s
                   FROM shipment
                   LEFT JOIN (SELECT shipment, SUM(sum_) as s
                   FROM shipment_pay GROUP BY shipment) AS sp
                   ON shipment.id_ =sp.shipment """
    sql_list_paid = """SELECT id_, name, sum_, datetime(date_,'unixepoch','localtime'),
                   sp.s
                   FROM shipment
                   LEFT JOIN (SELECT shipment, SUM(sum_) as s
                   FROM shipment_pay GROUP BY shipment) AS sp
                   ON shipment.id_ =sp.shipment WHERE shipment.sum_ = sp.s"""

    sql_list_name = """SELECT id_, name FROM shipment"""
    sql_sum = """SELECT sum_ FROM shipment WHERE id_ = ?"""

    sql_actions = """WITH things AS (SELECT id_ , shipment, date_ FROM thing WHERE shipment = ?)

                     SELECT shipment, '_',datetime(date_,'unixepoch', 'localtime'),
                            '0', sum_, date_
                     FROM shipment_pay WHERE shipment = ?

                     UNION

                     SELECT things.shipment, things.id_,
                            datetime(pay.date_,'unixepoch', 'localtime'),
                             pay.sum_, '0', things.date_
                     FROM things
                     JOIN pay ON things.id_ = pay.thing AND  pay.date_ > things.date_

                     UNION

                     SELECT things.shipment, things.id_,
                             datetime(things.date_,'unixepoch', 'localtime'),
                             SUM(pay.sum_), '0', things.date_
                     FROM things
                     JOIN pay ON things.id_ = pay.thing AND  pay.date_ <=things.date_
                     GROUP BY things.id_

                     ORDER BY date_
                     """

    sql_actions_old = """SELECT shipment, datetime(date_,'unixepoch', 'localtime'),
                            '0', sum_, date_
                     FROM shipment_pay WHERE shipment = ?
                     UNION
                     SELECT shipment, datetime(date_,'unixepoch', 'localtime'),
                             sum_, '0', date_
                     FROM (SELECT id_ , shipment FROM thing WHERE shipment = ?
                           ) as t
                     JOIN pay ON t.id_ = pay.thing



                     ORDER BY date_
                     """
    sql_total = """SELECT shipment.id_, shipment.name_ SUM(shipment_pay.sum_) FROM shipmetn_pay GROUP BY shipment
            LEFT JOIN shipment ON shipment_pay.shipment = shipment.id_"""

    @staticmethod
    def check_params(name, sum_, date):
        try:
            int(date)
            return name and sum_ > 0
        except ValueError:
            return False

    def add(self, name, sum_, date):
        if self.check_params(name, sum_, date):
            self._execute(self.sql_add, name, sum_, date)
        else:
            self.msg("wrong param")

    def update(self, id_, name, sum_, date):
        if self.check_params(name, sum_, date):
            self._execute(self.sql_upd, sum_, date, name, id_)
        else:
            self.msg("wrong param")

    def delete(self, id_):
        self._execute(self.sql_del, id_)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def list(self):
        return self._get_all(self.sql_list)

    def list_paid(self):
        return self._get_all(self.sql_list_paid)

    def sum(self, id_):
        return int(self._get_one(self.sql_sum, id_)[0])

    def actions(self, shipment):
        res = self._get_all(self.sql_actions, shipment, shipment)
        if not res:
            return
        x = []
        s = 0  # сальдо

        for action in res:
            thing_pay = int(action[3])  # оплаты по товарам
            shipment_pay = int(action[4])  # оплата по поставке
            round_founds = 0               # средства прошедшие "круг"
            if s < 0 < thing_pay:  # thing_pay > 0 and s < 0:
                round_founds = thing_pay if thing_pay < (-s) else -s
            elif shipment_pay > 0 and s > 0:
                round_founds = shipment_pay if shipment_pay < s else s
            s = s + thing_pay - shipment_pay
            if round_founds:
                x.append((action[0], action[1], action[2],  thing_pay, shipment_pay, s, round_founds))
        return x


class ShipmentPay(DbItem):

    sql_add = "INSERT INTO shipment_pay (sum_, date_, shipment) VALUES (?,?,?) "
    sql_upd = """UPDATE shipment_pay SET sum_ = ?, date_= ?, shipment = ?
                 WHERE id_ = ?"""
    sql_del = "DELETE FROM shipment_pay WHERE id_ = ?"
    sql_list = "SELECT shipment_pay.id_, " \
               "datetime(shipment_pay.date_,'unixepoch','localtime'), " \
               "shipment.name, shipment_pay.sum_ " \
               "FROM shipment_pay " \
               "LEFT JOIN shipment ON shipment_pay.shipment = shipment.id_"
    sql_get = "SELECT id_, sum_, date_, shipment FROM shipment_pay WHERE id_ = ?"
    sql_paid = """SELECT SUM(sum_) FROM shipment_pay WHERE shipment = ?"""

    def list(self):
        return self._get_all(self.sql_list)

    def add_no_commit(self, sum_, date_, shipment):
        return self._execute_no_commit(self.sql_add, sum_, date_, shipment)

    def upd_no_commit(self, id_, sum_, date_, shipment):
        return self._execute_no_commit(self.sql_upd, sum_, date_, shipment, id_)

    def get(self, id_):
        return self._get_one(self.sql_get, id_)

    def delete(self, id_):
        self._execute(self.sql_del, id_)

    def paid(self, shipment):
        res = self._get_one(self.sql_paid, shipment)
        return int(res[0]) if res[0] else 0


if __name__ == "__main__":
    create_db(dbFile)
