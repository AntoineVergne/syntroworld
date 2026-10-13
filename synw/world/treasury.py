"""The Treasury (03 §5.5): identical inflows in every world, never below 0.

A payment it cannot make in full is reduced pro rata and the cut is logged.
"""

GOODS = ("food", "energy", "artifact")


class Treasury:
    def __init__(self, balance=0, log=None, now=lambda: 0):
        self.balance = int(balance)
        self.goods = {g: 0 for g in GOODS}
        self.log = log
        self.now = now
        self.inflow_today = 0
        self.outflow_today = 0
        self.history = []  # (day, inflow, outflow, balance)

    def _emit(self, type_, payload):
        if self.log is not None:
            self.log.emit(self.now(), type_, "treasury", payload)

    def collect(self, amount, kind, frm=None):
        amount = int(amount)
        if amount <= 0:
            return 0
        self.balance += amount
        self.inflow_today += amount
        self._emit("treasury_in", {"amount": amount, "kind": kind, "from": frm,
                                   "balance": self.balance})
        return amount

    def receive_goods(self, goods, kind, frm=None):
        for g, q in goods.items():
            self.goods[g] = self.goods.get(g, 0) + q
        self._emit("treasury_goods", {"goods": dict(goods), "kind": kind, "from": frm})

    def pay_many(self, payments, kind):
        """Pay ``[(recipient, amount)]``; returns the amounts paid, pro rata if short."""
        payments = [(r, int(a)) for r, a in payments if int(a) > 0]
        due = sum(a for _, a in payments)
        if due <= 0:
            return []
        if due <= self.balance:
            paid = [a for _, a in payments]
        else:
            avail = self.balance
            paid = [a * avail // due for _, a in payments]
            self._emit("treasury_shortfall", {"kind": kind, "due": due, "paid": sum(paid),
                                              "balance": self.balance})
        total = sum(paid)
        self.balance -= total
        self.outflow_today += total
        out = []
        for (r, a), p in zip(payments, paid):
            out.append((r, p))
            if p > 0:
                self._emit("treasury_out", {"amount": p, "due": a, "kind": kind, "to": r,
                                            "balance": self.balance})
        return out

    def pay(self, recipient, amount, kind):
        res = self.pay_many([(recipient, amount)], kind)
        return res[0][1] if res else 0

    def end_day(self, day):
        self.history.append((day, self.inflow_today, self.outflow_today, self.balance))
        self.inflow_today = 0
        self.outflow_today = 0

    def recent_flows(self, days=3):
        h = self.history[-days:]
        if not h:
            return 0, 0
        return sum(x[1] for x in h) // len(h), sum(x[2] for x in h) // len(h)

    def state(self):
        return {"balance": self.balance, "goods": dict(self.goods)}
