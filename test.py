# coding:utf8
"""
Генерация тестовых данных
"""
from time import mktime
from random import randint, choice, seed


def get_random_string(min_, max_):
    name = ""
    c = tuple(u"абявюгедежазияикалеменопористуфахоцичэюяшащ")
    for l in xrange(randint(min_, max_)):
        name += choice(c)
    return name


class TestUser(object):
    def __init__(self, user):
        self.user = user

    def clear(self):
        self.user._conn.execute("DELETE FROM user ")

    def generate(self, count=1):
        for i in xrange(count):
            self.user.add_nocommit(get_random_string(4, 8),
                                   get_random_string(6, 10),
                                   randint(18, 77)
                                   )
        self.user._conn.commit()


class ThingType(object):

    def __init__(self, thing_type):
        self.type = thing_type

    def generate(self, count=1):
        for i in xrange(count):
            self.type.add_nocommit("Type_" + get_random_string(4, 6))
        self.type._conn.commit()

    def clear(self):
        self.type._conn.execute("DELETE FROM thing_type")


class TestThing(object):

    def __init__(self, thing, user,  type):
        self.thing = thing
        self.user = user
        self.type = type

    def generate(self, count=1):
        users = self.user.get_list_names()
        types = self.type.get_list()
        for i in xrange(count):
            self.thing.add_nocommit(
                "Thng_" + get_random_string(4, 8),
                choice(types)[0],
                choice(users)[0],
                randint(1444917614, 1476540014),
                randint(10, 90)*100
            )

    def clear(self):
        self.type._conn.execute("DELETE FROM thing")


class TestPay(object):

    def __init__(self, pay, user, thing):
        self.pay = pay
        self.user = user
        self.thing = thing

    def clear(self):
        self.pay._conn.execute("DELETE FROM pay")

    def generate(self, count=1, year=2015):
        start = int(mktime((year, 1, 1, 0, 0, 0, 0, 0, 0)))
        stop = int(mktime((year+1, 1, 1, 0, 0, 0, 0, 0, 0)))
        step = 86400

        things = [list(t) for t in self.thing.get_unpaid_id()]
        users = self.user.get_list_names()

        # словарь {день:количество покупок}, если покупок больше 1000, день изымается из словаря
        # pay_count = {}
        # for day in xrange(365):
        #    p = self.pay.count_in_range(start + day * step, start + day * step + step)
        #   if p < 999:
        #       pay_count[day] = p
        #       print "day- ok 2 {} {}".format(start, start + 365 * step + step)

        p = self.pay.group_by_date(start, stop)
        pay_count = dict(p)

        # print "day- ok 2 {} {}".format(start, stop)
        # for day in xrange(366):
        #  print "{} {} {}".format(day, pay_count.get(day,"-"), pay_count2.get(day,"-"))

        for i in xrange(count):
            if not things:
                print "no more things"
                return
            if not pay_count:
                print "no more days"
                return
            # x = randint(0,len(things))
            # thing = things[x]
            thing = choice(things)
            if thing[2] == 9:       # pay_count
                sum_ = thing[1]     # cost_remain
                things.remove(thing)
            # print "tester pc9: {}".format(sum_)
            # del things[x]
            elif thing[1] == 0:
                print "WTF??? {} {} / {}".format(thing[0], thing[1], thing[2])
                things.remove(thing)
                # del things[x]
            else:
                sum_ = randint(1, thing[1])
                thing[1] -= sum_
                thing[2] += 1
                if thing[1] == 0:
                    # del things[x]
                    things.remove(thing)

            day = choice(pay_count.keys())
            pay_count[day] += 1
            if pay_count[day] > 999:
                pay_count.pop(day)

            # print "add {} / {}".format(i, count)
            self.pay.add_nocommit(start + day * step + randint(0, step),
                                  get_random_string(4, 12),
                                  choice(users)[0],
                                  thing[0],
                                  sum_
                                  )
        print "done"


class Tester(object):
    def __init__(self, db):
        seed()
        self.db = db
        self.user = TestUser(db.user)
        self.type = ThingType(db.type)
        self.thing = TestThing(db.thing, db.user, db.type)
        self.pay = TestPay(db.pay, db.user, db.thing)

    def commit(self):
        self.db._conn.commit()

    def rollback(self):
        self.db._conn.rollback()
