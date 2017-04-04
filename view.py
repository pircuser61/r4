# -*- coding: utf-8 -*-

from time import mktime
import tornado.ioloop
import tornado.web
import os

from data import DB
from test import Tester


html_folder = os.path.join(os.path.dirname(__file__), 'html\\')


class RequestHandler(tornado.web.RequestHandler):
    """заглушка для абстрактных методов tornado.web.RequestHandler, подавлялка варнингов"""
    def head(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def get(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def post(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def delete(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def patch(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def put(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def options(self, *args, **kwargs):
        self.render(html_folder + "main.txt")

    def data_received(self, chunk):
        self.render(html_folder + "main.txt")


class Main(RequestHandler):
    def get(self):
        self.render(html_folder + "main.txt")


class Wrong(RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        self.render(html_folder + "wrongRequest.txt")


class UserView(RequestHandler):
    def get(self, id_):
        obj = db.user
        if id_:
            self.render(html_folder + "user.txt",
                        user=obj.get(id_),
                        messages=obj.get_message_str()
                        )
        else:
            page = int(self.get_argument("page", default=0))
            if page < 0:
                page = 0
            count = obj.count()
            self.render(html_folder + "userList.txt",
                        users=obj.get_list(page * 10),
                        messages=obj.get_message_str(),
                        page=page,
                        pageCount=(count - 1) // 10,
                        userCount=count
                        )

    def post(self, id_):
        obj = db.user
        try:
            cmd = self.get_argument("cmd")
        except tornado.web.MissingArgumentError:
            self.redirect("/wrongRequest/")
        else:
            if cmd == "add":
                name = self.get_argument("name")
                surname = self.get_argument("surname")
                age = self.get_argument("age")
                obj.add(name, surname, age)

            elif cmd == "upd":
                id_ = self.get_argument("id")
                name = self.get_argument("name")
                surname = self.get_argument("surname")
                age = self.get_argument("age")
                obj.update(id_, name, surname, age)

            elif cmd == "del":
                id_ = self.get_argument("id")
                obj.delete(id_)

            self.redirect("/user/")


class ThingTypeView(RequestHandler):
    def get(self, id_):
        if id_:
            self.render(html_folder + "thingType.txt",
                        thingType=db.type.get(id_),
                        messages=db.type.get_message_str()
                        )
        else:
            self.render(html_folder + "thingTypeList.txt",
                        types=db.type.get_list(),
                        messages=db.type.get_message_str()
                        )

    def post(self, param):
        try:
            cmd = self.get_argument("cmd")
        except tornado.web.MissingArgumentError:
            self.redirect("/wrongRequest/")
        else:
            if cmd == "add":
                name = self.get_argument("name")
                db.type.add(name)

            if cmd == "upd":
                id_ = self.get_argument("id")
                name = self.get_argument("name")
                db.type.update(id_, name)

            if cmd == "del":
                id_ = self.get_argument("id")
                db.type.delete(id_)

            self.redirect("/thing_type/")


class ThingView(RequestHandler):

    def get(self, id_):
        obj = db.thing
        users = db.user
        types = db.type
        messages = obj.get_message_str() + \
            users.get_message_str() + \
            types.get_message_str()
        if id_:
            self.render(html_folder + "thing.txt",
                        thing=obj.get(id_),
                        users=users.get_list(),
                        types=types.get_list(),
                        messages=messages
                        )
        else:
            page = int(self.get_argument("page", default='0'))
            start = page * 10
            if start < 0:
                start = 0
            messages = obj.get_message_str() + \
                users.get_message_str() + \
                types.get_message_str()
            self.render(html_folder + "thingList.txt",
                        things=obj.get_list(start),
                        thingCount=obj.count(),
                        page=page,
                        users=users.get_list(),
                        types=types.get_list(),
                        messages=messages
                        )

    def post(self, id_):
        obj = db.thing
        try:
            cmd = self.get_argument("cmd")

        except tornado.web.MissingArgumentError:
            self.redirect("/wrongRequest/")
        else:
            if cmd == "add":
                name = self.get_argument("name")
                type_ = self.get_argument("type_")
                user = self.get_argument("user")
                date = self.get_argument("date")
                sum_ = self.get_argument("sum_")
                info = self.get_argument("info")
                shipment = self.get_argument("shipment")
                db.thing_add(name, type_, user, shipment, date, sum_, info)

            elif cmd == "del":
                id_ = self.get_argument("id")
                obj.delete(id_)

            elif cmd == "upd":
                id_ = self.get_argument("id_")
                name = self.get_argument("name")
                type_ = self.get_argument("type_")
                user = self.get_argument("user")
                date = self.get_argument("date")
                sum_ = self.get_argument("sum_")
                info = self.get_argument("info")
                shipment = self.get_argument("shipment")

                remain = int(sum_) - db.pay.paid(id_)
                if remain >= 0:
                    obj.update(id_, name, type_, user, shipment, date, sum_, remain, info)
                else:
                    obj.msg("new sum < paid")
            self.redirect("/thing/")


class PayView(RequestHandler):
    cols = ("id_", "date_", "caption", "user", "thing", "thing_id", "sum_")
    cols2 = ("id_", "date_", "caption", "user", "thing", "sum_")

    def get(self, id_):
        pay = db.pay
        users = db.user
        things = db.thing
        if id_:
            p = pay.get(id_)
            if p:
                pay_dict = dict(zip(self.cols2, p))
            else:
                pay_dict = None
            messages = pay.get_message_str() +\
                things.get_message_str() +\
                users.get_message_str()
            self.render(html_folder + 'pay.txt',
                        pay=pay_dict,
                        users=users.get_list_names(),
                        things=things.get_list_names(),
                        messages=messages
                        )

        else:
            page = self.get_argument("page", default="0")
            start = int(page) * 10 if page else 0
            filter_user = self.get_argument("filter_user", default="")
            filter_thing = self.get_argument("filter_thing", default="")
            year = self.get_argument("year", default="2015")
            day = self.get_argument("day", default="")
            if day and year:
                filter_begin = int(mktime((int(year), 1, 0, 0, 0, 0, 0, 0, 0))) + int(day)*86400
                filter_end = filter_begin + 86400
            else:
                filter_begin = 0
                filter_end = 0
            pay_list = pay.get_filtered_list(start,
                                             filter_user,
                                             filter_thing,
                                             filter_begin,
                                             filter_end,
                                             )
            if pay_list:
                pay_dict = [dict(zip(self.cols, st)) for st in pay_list]
            else:
                pay_dict = None
            messages = pay.get_message_str() +\
                things.get_message_str() +\
                users.get_message_str()
            self.render(html_folder + 'payList.txt',
                        count=pay.count(),
                        page=page,
                        filter_user=filter_user,
                        filter_thing=filter_thing,
                        day=day,
                        year=year,
                        pays=pay_dict,
                        users=users.get_list_names(),
                        things=things.get_list_names(),
                        messages=messages
                        )

    def post(self, param):
        obj = db.pay
        try:
            cmd = self.get_argument("cmd")
        except tornado.web.MissingArgumentError:
            self.redirect("/wrongRequest/")
        else:
            if cmd == "add":
                db.pay_add(self.get_argument("date"),
                           self.get_argument("caption"),
                           self.get_argument("user"),
                           self.get_argument("thing"),
                           self.get_argument("sum_")
                           )

            elif cmd == "upd":
                db.pay_upd(self.get_argument("id_"),
                           self.get_argument("date"),
                           self.get_argument("caption"),
                           self.get_argument("user"),
                           self.get_argument("thing"),
                           self.get_argument("sum_")
                           )

            elif cmd == "del":
                obj.delete(self.get_argument("id_"))

        self.redirect("/pay/")


class ShipmentPayView(RequestHandler):

    def get(self, id_):
        if id_:
            self.render(html_folder + "shipmentPay.txt",
                        shipment_pay=db.shipment_pay.get(id_),
                        messages=db.shipment_pay.get_message_str()
                        )
        else:
            self.render(html_folder + "shipmentPayList.txt",
                        list=db.shipment_pay.list(),
                        messages=db.shipment_pay.get_message_str()
                        )

    def post(self, id_):
        cmd = self.get_argument("cmd", default="")
        if cmd == "add":
            db.shipment_pay_add(self.get_argument("sum_"),
                                self.get_argument("date"),
                                self.get_argument("shipment")
                                )
        elif cmd == 'upd':
            db.shipment_pay_upd(self.get_argument("id_"),
                                self.get_argument("sum_"),
                                self.get_argument("date"),
                                self.get_argument("shipment")
                                )
        elif cmd == "del":
            db.shipment_pay.delete(self.get_argument("id_"))

        self.redirect("/shipment_pay/")


class ShipmentView(RequestHandler):

    def get(self, id_):
        if id_:
            self.render(html_folder + "shipment.txt",
                        shipment=db.shipment.get(id_),
                        messages=db.shipment.get_message_str(),
                        actions=db.shipment.actions(id_)
                        )
        else:
            self.render(html_folder + "shipmentList.txt",
                        list=db.shipment.list(),
                        messages=db.shipment.get_message_str()
                        )

    def post(self, id_):
        obj = db.shipment
        cmd = self.get_argument("cmd", default="")
        if cmd == "add":
            obj.add(self.get_argument("name"),
                    self.get_argument("sum_"),
                    self.get_argument("date")
                    )

        elif cmd == "del":
            obj.delete(self.get_argument("id_"))

        elif cmd == "upd":
            obj.update(self.get_argument("id_"),
                       self.get_argument("name"),
                       self.get_argument("sum_"),
                       self.get_argument("date_")
                       )

        self.redirect("/shipment/")


class TesterView(RequestHandler):

    def get(self):
        self.render(html_folder + "tester.txt",
                    thing_count=db.thing.count(),
                    user_count=db.user.count(),
                    type_count=db.type.count(),
                    pay_count=db.pay.count()
                    )

    def post(self):
        cmd = self.get_argument("cmd", default="")

        if cmd == "commit":
            t.commit()
        elif cmd == "rollback":
            t.rollback()

        elif cmd == "user_generate":
            t.user.generate(int(self.get_argument("user_count", default="1")))
        elif cmd == "user_clear":
            t.user.clear()

        elif cmd == "type_generate":
            t.type.generate(int(self.get_argument("type_count", default="1")))
        elif cmd == "type_clear":
            t.type.clear()

        elif cmd == "thing_generate":
            t.thing.generate(int(self.get_argument("thing_count", default="1")))
        elif cmd == "thing_clear":
            t.thing.clear()

        elif cmd == "pay_generate":
            t.pay.generate(int(self.get_argument("pay_count", default="1")))
        elif cmd == "pay_clear":
            t.pay.clear()

        self.redirect("/tester/")


class Reports(RequestHandler):
    def get(self):
        cmd = self.get_argument("cmd", default="")
        if cmd == "unpaid":
            self.render(html_folder + "unpaid.txt",
                        things=db.thing.get_unpaid(),
                        messages=db.thing.get_message_str()
                        )
        elif cmd == "top_spend":
            self.render(html_folder + "top_spend.txt",
                        items=db.user.get_top_spend(),
                        messages=db.user.get_message_str(),
                        title=u"Больше всех потратили"
                        )
        elif cmd == "top_spend_1":
            self.render(html_folder + "top_spend.txt",
                        items=db.user.get_top_spend_1(),
                        messages=db.user.get_message_str(),
                        title=u"Больше всех потратили (медленный запрос)"
                        )
        elif cmd == "spend_on_other":
            self.render(html_folder + "top_spend.txt",
                        items=db.user.get_top_spend_on_other(),
                        messages=db.user.get_message_str(),
                        title=u"На других"
                        )
        elif cmd == "cadger":
            self.render(html_folder + "top_spend.txt",
                        items=db.user.get_cadger(),
                        messages=db.user.get_message_str(),
                        title=u"Попрашайки"
                        )
        elif cmd == "shipment_paid":
            self.render(html_folder + "shipmentList.txt",
                        list=db.shipment.list_paid(),
                        messages="Оплаченные" + db.shipment.get_message_str()
                        )

        elif cmd == "thing_paid":
            self.render(html_folder + "thingPaidList.txt",
                        list=db.thing.list_paid(),
                        messages="Оплаченные" + db.thing.get_message_str()
                        )

        elif cmd == "thing_unpaid":
            self.render(html_folder + "thingPaidList.txt",
                        list=db.thing.list_unpaid(),
                        messages="Неоплаченные" + db.thing.get_message_str()
                        )

        elif cmd == "shipment_total":
            self.render(html_folder + "shipmentTotal.txt",
                        list=db.thing.list_total(),
                        messages="total " + db.thing.get_message_str()
                        )

        elif cmd == "shipment_full_paid":
            self.render(html_folder + "shipmentTotal.txt",
                        list=db.thing.list_full_paid(),
                        messages="full_paid " + db.thing.get_message_str()
                        )
        else:
            self.render(html_folder + "reports.txt")


if __name__ == "__main__":
    db = DB()
    t = Tester(db)
    app = tornado.web.Application(
        [
            (r"/", Main),
            (r"/user/([0-9]*)", UserView),
            (r"/thing_type/([0-9]*)", ThingTypeView),
            (r"/thing/([0-9]*)", ThingView),
            (r"/pay/([0-9]*)", PayView),
            (r"/shipment/([0-9]*)", ShipmentView),
            (r"/shipment_pay/([0-9]*)", ShipmentPayView),
            (r"/wrongRequest/", Wrong),
            (r"/tester/", TesterView),
            (r"/reports/", Reports),
         ],
        debug=True)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
