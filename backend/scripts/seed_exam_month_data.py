# -*- coding: utf-8 -*-
"""生成“考试月”月度报告演示数据。

使用方式：
    python backend/scripts/seed_exam_month_data.py --month 2026-06 --dry-run
    python backend/scripts/seed_exam_month_data.py --month 2026-06

设计边界：
    - 不清理、不删除现有数据。
    - 不创建或覆盖管理员账号。
    - 不写入任何密钥。
    - 只新增/复用带 DEMO_EXAM_MONTH 标识的数据，便于后续识别。
"""

from __future__ import annotations

import argparse
import random
import sys
from calendar import monthrange
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.book import Book  # noqa: E402
from models.book_request import BookRequest  # noqa: E402
from models.borrow import Borrow  # noqa: E402
from models.category import Category  # noqa: E402
from models.notification import Notification  # noqa: E402
from models.reservation import Reservation  # noqa: E402
from models.seat import Seat  # noqa: E402
from models.seat_repair import SeatRepair  # noqa: E402
from models.user import User  # noqa: E402


DEMO_MARK = "[DEMO_EXAM_MONTH]"
RANDOM_SEED = 20260709

CATEGORIES = [
    "计算机",
    "数学",
    "英语",
    "专业课",
    "文学",
    "历史",
    "哲学",
    "经济",
    "自然科学",
]

PROFESSIONAL_CATEGORIES = {"计算机", "数学", "英语", "专业课"}

HOT_BOOKS = [
    ("数据结构与算法分析", "Mark Allen Weiss", "计算机", "机械工业出版社", 2021, 1),
    ("计算机网络", "谢希仁", "计算机", "电子工业出版社", 2022, 2),
    ("操作系统", "汤小丹", "计算机", "西安电子科技大学出版社", 2021, 1),
    ("数据库系统概论", "王珊", "计算机", "高等教育出版社", 2023, 0),
    ("高等数学", "同济大学数学系", "数学", "高等教育出版社", 2022, 2),
    ("线性代数", "同济大学数学系", "数学", "高等教育出版社", 2021, 2),
    ("概率论与数理统计", "浙江大学", "数学", "高等教育出版社", 2022, 1),
    ("大学英语四级真题", "新东方考试研究中心", "英语", "群言出版社", 2024, 1),
    ("大学英语六级真题", "新东方考试研究中心", "英语", "群言出版社", 2024, 0),
    ("人工智能：一种现代方法", "Stuart Russell", "计算机", "人民邮电出版社", 2022, 2),
    ("Python编程：从入门到实践", "Eric Matthes", "计算机", "人民邮电出版社", 2023, 1),
    ("408计算机考研真题", "王道论坛", "专业课", "电子工业出版社", 2024, 0),
]

SUPPORT_BOOKS = [
    ("计算机组成原理", "唐朔飞", "专业课", "高等教育出版社", 2021, 6),
    ("软件工程导论", "张海藩", "专业课", "清华大学出版社", 2020, 8),
    ("离散数学", "左孝凌", "数学", "上海科学技术文献出版社", 2021, 7),
    ("考研英语阅读理解", "何凯文", "英语", "中国原子能出版社", 2024, 5),
    ("现代文学三十年", "钱理群", "文学", "北京大学出版社", 2019, 12),
    ("中国通史", "吕思勉", "历史", "中华书局", 2020, 10),
    ("西方哲学史", "罗素", "哲学", "商务印书馆", 2018, 9),
    ("宏观经济学", "曼昆", "经济", "中国人民大学出版社", 2021, 8),
    ("普通生物学", "陈阅增", "自然科学", "高等教育出版社", 2020, 9),
    ("物理学基础", "哈里德", "自然科学", "机械工业出版社", 2020, 7),
]

ROOMS = [
    ("二楼自习室", 2, "B201", 10, 7, "普通座位"),
    ("三楼考研专区", 3, "C301", 12, 9, "安静区座位"),
    ("电子阅览室", 2, "E201", 8, 8, "电子阅览座位"),
    ("安静学习区", 4, "D401", 8, 5, "靠窗座位"),
    ("研讨室", 2, "R201", 6, 3, "研讨室座位"),
]

BOOK_REQUEST_TITLES = [
    ("408计算机考研真题", "王道论坛", "考试月专业课备考需求集中，建议增加复本。"),
    ("大学英语六级真题", "新东方考试研究中心", "六级考试前借阅需求高，现有馆藏不足。"),
    ("高等数学辅导讲义", "张宇", "期末复习和考研复习均需要。"),
    ("操作系统课程设计", "高校课程组", "课程设计周参考资料不足。"),
    ("数据库课程设计案例", "李明", "数据库课程实践和期末项目需要。"),
    ("教师资格考试资料", "考试研究中心", "师范生备考需求。"),
]

REPAIR_DESCRIPTIONS = [
    "插座损坏，无法给电脑充电",
    "台灯故障，晚间学习照明不足",
    "桌面松动，影响长时间复习",
    "网络不稳定，电子资源访问中断",
    "座椅损坏，坐垫松动",
]

NOTIFICATION_TEMPLATES = [
    ("借阅审核通知", "borrow", "您的考试月借阅申请已通过，请及时到馆领取。"),
    ("到期提醒", "return", "您借阅的复习资料即将到期，如需继续使用请及时续借。"),
    ("逾期提醒", "overdue", "您有考试月借阅图书已逾期，请尽快归还。"),
    ("座位预约通知", "reservation", "您预约的自习座位已确认，请按时签到。"),
    ("报修处理通知", "system", "您反馈的座位问题已进入处理流程。"),
    ("考试月延长开放时间通知", "system", "考试月图书馆晚间开放时间延长至 22:30。"),
    ("热门图书补充通知", "system", "部分热门专业书正在加急补充复本。"),
]


@dataclass
class SeedStats:
    users: int = 0
    categories: int = 0
    books: int = 0
    seats: int = 0
    borrows: int = 0
    reservations: int = 0
    book_requests: int = 0
    repairs: int = 0
    notifications: int = 0
    skipped_month_blocks: int = 0

    def as_lines(self):
        return [
            f"用户数: {self.users}",
            f"分类数: {self.categories}",
            f"图书数: {self.books}",
            f"座位数: {self.seats}",
            f"借阅记录数: {self.borrows}",
            f"座位预约数: {self.reservations}",
            f"荐购数: {self.book_requests}",
            f"报修数: {self.repairs}",
            f"通知数: {self.notifications}",
            f"已跳过的既有月份数据块: {self.skipped_month_blocks}",
        ]


def parse_month(month_text: str) -> date:
    try:
        year, month = map(int, month_text.split("-"))
        if month < 1 or month > 12:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise argparse.ArgumentTypeError("month 参数格式应为 YYYY-MM")
    return date(year, month, 1)


def add_months(value: date, delta: int) -> date:
    month_index = value.year * 12 + (value.month - 1) + delta
    year = month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def previous_month(today: date | None = None) -> date:
    today = today or date.today()
    return add_months(date(today.year, today.month, 1), -1)


def month_range(month: date):
    end_day = monthrange(month.year, month.month)[1]
    start_date = date(month.year, month.month, 1)
    end_date = date(month.year, month.month, end_day)
    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date, time.max)
    return start_date, end_date, start_at, end_at


def month_label(month: date) -> str:
    return month.strftime("%Y-%m")


def random_day(month: date) -> date:
    return date(month.year, month.month, random.randint(1, monthrange(month.year, month.month)[1]))


def random_datetime(month: date, start_hour: int = 8, end_hour: int = 21) -> datetime:
    day = random_day(month)
    hour = random.randint(start_hour, end_hour)
    minute = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
    return datetime.combine(day, time(hour, minute))


def weighted_choice(items):
    choices, weights = zip(*items)
    return random.choices(choices, weights=weights, k=1)[0]


def get_or_create_category(name: str, stats: SeedStats) -> Category:
    category = Category.query.filter_by(name=name).first()
    if category:
        return category

    category = Category(name=name, is_deleted=False)
    db.session.add(category)
    stats.categories += 1
    return category


def create_users(stats: SeedStats):
    students = []
    teachers = []

    for index in range(1, 49):
        username = f"demo_exam_student_{index:03d}"
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                real_name=f"考试月学生{index:03d}",
                role="student",
                status="active",
                phone=f"13960{index:06d}"[-11:],
                email=f"{username}@demo.local",
            )
            user.set_password("Demo123456")
            db.session.add(user)
            stats.users += 1
        if user.role == "student" and user.status == "active":
            students.append(user)

    for index in range(1, 8):
        username = f"demo_exam_teacher_{index:03d}"
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                real_name=f"考试月教师{index:03d}",
                role="teacher",
                status="active",
                phone=f"13870{index:06d}"[-11:],
                email=f"{username}@demo.local",
            )
            user.set_password("Demo123456")
            db.session.add(user)
            stats.users += 1
        if user.role == "teacher" and user.status == "active":
            teachers.append(user)

    return students, teachers


def create_books(category_map: dict[str, Category], stats: SeedStats):
    books_by_category: dict[str, list[Book]] = defaultdict(list)
    hot_books: list[Book] = []

    all_books = HOT_BOOKS + SUPPORT_BOOKS
    for index, (title, author, category_name, publisher, year, stock) in enumerate(all_books, start=1):
        isbn = f"DEMO-EXAM-{index:03d}"
        book = Book.query.filter_by(isbn=isbn).first()
        category = category_map[category_name]
        if not book:
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                publish_year=year,
                stock=stock,
                category_id=category.id,
                location=f"考试月演示专区-{category_name}",
                description=f"{DEMO_MARK} 考试月演示馆藏：{title}",
                is_deleted=False,
            )
            db.session.add(book)
            stats.books += 1
        elif book.isbn.startswith("DEMO-EXAM-"):
            book.stock = stock
            book.category_id = category.id
            book.is_deleted = False
            book.location = f"考试月演示专区-{category_name}"
            book.description = f"{DEMO_MARK} 考试月演示馆藏：{title}"

        books_by_category[category_name].append(book)
        if index <= len(HOT_BOOKS):
            hot_books.append(book)

    return books_by_category, hot_books


def create_seats(stats: SeedStats):
    seats: list[Seat] = []
    power_seats: list[Seat] = []
    non_power_seats: list[Seat] = []

    for room_name, floor, prefix, count, power_count, feature_name in ROOMS:
        for index in range(1, count + 1):
            seat_number = f"EXAM-{prefix}-{index:02d}"
            has_power = index <= power_count
            description = f"{DEMO_MARK} {feature_name}，考试月演示座位"
            seat = Seat.query.filter_by(seat_number=seat_number).first()
            if not seat:
                seat = Seat(
                    seat_number=seat_number,
                    room_name=room_name,
                    floor=floor,
                    status="available",
                    has_power=has_power,
                    description=description,
                )
                db.session.add(seat)
                stats.seats += 1
            elif seat.seat_number.startswith("EXAM-"):
                seat.room_name = room_name
                seat.floor = floor
                seat.status = "available"
                seat.has_power = has_power
                seat.description = description

            seats.append(seat)
            if has_power:
                power_seats.append(seat)
            else:
                non_power_seats.append(seat)

    return seats, power_seats, non_power_seats


def select_book_for_borrow(
    books_by_category: dict[str, list[Book]],
    hot_books: list[Book],
    exam_month: bool,
):
    if exam_month:
        category_name = weighted_choice([
            ("计算机", 28),
            ("数学", 18),
            ("英语", 14),
            ("专业课", 12),
            ("文学", 7),
            ("历史", 6),
            ("哲学", 5),
            ("经济", 5),
            ("自然科学", 5),
        ])
        if category_name in PROFESSIONAL_CATEGORIES and random.random() < 0.72:
            candidates = [book for book in hot_books if book.category and book.category.name == category_name]
            if candidates:
                return random.choice(candidates)
    else:
        category_name = weighted_choice([
            ("计算机", 16),
            ("数学", 10),
            ("英语", 10),
            ("专业课", 10),
            ("文学", 14),
            ("历史", 12),
            ("哲学", 10),
            ("经济", 10),
            ("自然科学", 8),
        ])

    return random.choice(books_by_category[category_name])


def select_active_user(students, teachers, exam_month: bool):
    if exam_month:
        return random.choice(students[:42] if random.random() < 0.90 else teachers[:5])
    return random.choice(students[:30] if random.random() < 0.82 else teachers)


def month_has_demo_borrows(start_at: datetime, end_at: datetime) -> bool:
    return db.session.query(Borrow.id).join(Book, Borrow.book_id == Book.id).filter(
        Book.isbn.like("DEMO-EXAM-%"),
        Borrow.create_time >= start_at,
        Borrow.create_time <= end_at,
    ).first() is not None


def create_borrows_for_month(
    month: date,
    exam_month: bool,
    students,
    teachers,
    books_by_category,
    hot_books,
    stats: SeedStats,
):
    _, _, start_at, end_at = month_range(month)
    if month_has_demo_borrows(start_at, end_at):
        stats.skipped_month_blocks += 1
        return

    valid_count = 190 if exam_month else random.randint(58, 72)
    pending_count = 16 if exam_month else random.randint(4, 7)
    status_weights = [
        ("returned", 48),
        ("borrowed", 28),
        ("overdue", 13 if exam_month else 8),
    ]

    for _ in range(valid_count):
        book = select_book_for_borrow(books_by_category, hot_books, exam_month)
        user = select_active_user(students, teachers, exam_month)
        borrow_at = random_datetime(month, 8, 20)
        status = weighted_choice(status_weights)
        renew_count = 0
        if random.random() < (0.29 if exam_month else 0.16):
            renew_count = random.choice([1, 1, 1, 2])

        if status == "returned":
            due_at = borrow_at + timedelta(days=30 + 10 * renew_count)
            return_at = borrow_at + timedelta(days=random.randint(6, 24 + 8 * renew_count))
            if return_at > due_at:
                return_at = due_at - timedelta(days=random.randint(0, 2))
        elif status == "overdue":
            last_day = monthrange(month.year, month.month)[1]
            borrow_day = random.randint(1, max(1, min(12, last_day - 5)))
            borrow_at = datetime.combine(
                date(month.year, month.month, borrow_day),
                time(random.randint(8, 17), random.choice([0, 15, 30, 45])),
            )
            due_day = min(last_day, borrow_day + random.randint(5, 14))
            due_at = datetime.combine(date(month.year, month.month, due_day), time(23, 59))
            return_at = None
        else:
            due_at = datetime.now() + timedelta(days=random.randint(8, 26))
            return_at = None

        borrow = Borrow(
            user_id=user.id,
            book_id=book.id,
            status=status,
            borrow_time=borrow_at,
            due_time=due_at,
            return_time=return_at,
            renew_count=renew_count,
            create_time=borrow_at - timedelta(hours=random.randint(2, 36)),
            update_time=borrow_at,
        )
        db.session.add(borrow)
        stats.borrows += 1

    for _ in range(pending_count):
        book = select_book_for_borrow(books_by_category, hot_books, exam_month)
        user = select_active_user(students, teachers, exam_month)
        create_at = random_datetime(month, 9, 21)
        borrow = Borrow(
            user_id=user.id,
            book_id=book.id,
            status="pending",
            borrow_time=None,
            due_time=None,
            return_time=None,
            renew_count=0,
            create_time=create_at,
            update_time=create_at,
        )
        db.session.add(borrow)
        stats.borrows += 1


def exam_month_hot_topup_count(start_at: datetime, end_at: datetime, admin_id: int | None) -> int:
    query = db.session.query(Borrow.id).join(Book, Borrow.book_id == Book.id).filter(
        Book.isbn.like("DEMO-EXAM-%"),
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(("borrowed", "returned", "overdue")),
    )
    if admin_id:
        query = query.filter(Borrow.review_admin_id == admin_id)
    else:
        marker_start = datetime.combine(start_at.date(), time(6, 1))
        marker_end = datetime.combine(start_at.date(), time(6, 59))
        query = query.filter(Borrow.create_time >= marker_start, Borrow.create_time <= marker_end)
    return query.count()


def ensure_exam_month_hot_book_topup(
    month: date,
    students,
    hot_books,
    admin_id: int | None,
    stats: SeedStats,
):
    """补充热门专业书借阅，保证考试月 Top10 明显偏专业书。

    该函数只追加 DEMO 数据，不删除旧数据。补充记录使用 review_admin_id 作为幂等标记；
    如果没有管理员，则使用特殊 create_time 时间窗作为幂等标记。
    """
    start_date, _, start_at, end_at = month_range(month)
    target_topup_count = 60
    existing = exam_month_hot_topup_count(start_at, end_at, admin_id)
    if existing >= target_topup_count:
        return

    professional_hot_books = [
        book
        for book in hot_books
        if book.category and book.category.name in PROFESSIONAL_CATEGORIES
    ]
    if not professional_hot_books:
        return

    needed = target_topup_count - existing
    status_weights = [
        ("returned", 52),
        ("borrowed", 30),
        ("overdue", 18),
    ]

    for index in range(needed):
        book = professional_hot_books[index % len(professional_hot_books)]
        user = students[index % min(len(students), 42)]
        borrow_day = 3 + (index % max(1, monthrange(month.year, month.month)[1] - 8))
        borrow_at = datetime.combine(
            date(month.year, month.month, borrow_day),
            time(random.choice([9, 10, 14, 15, 19, 20]), random.choice([0, 20, 40])),
        )
        status = weighted_choice(status_weights)
        renew_count = 1 if random.random() < 0.34 else 0

        if status == "returned":
            due_at = borrow_at + timedelta(days=30 + 10 * renew_count)
            return_at = borrow_at + timedelta(days=random.randint(8, 24))
        elif status == "overdue":
            due_day = min(monthrange(month.year, month.month)[1], borrow_day + random.randint(5, 11))
            due_at = datetime.combine(date(month.year, month.month, due_day), time(23, 59))
            return_at = None
        else:
            due_at = datetime.now() + timedelta(days=random.randint(10, 25))
            return_at = None

        marker_create_time = datetime.combine(start_date, time(6, 1)) + timedelta(minutes=index % 58)
        borrow = Borrow(
            user_id=user.id,
            book_id=book.id,
            status=status,
            borrow_time=borrow_at,
            due_time=due_at,
            return_time=return_at,
            review_admin_id=admin_id,
            renew_count=renew_count,
            create_time=marker_create_time,
            update_time=borrow_at,
        )
        db.session.add(borrow)
        stats.borrows += 1


def month_has_demo_reservations(start_date: date, end_date: date) -> bool:
    return db.session.query(Reservation.id).join(Seat, Reservation.seat_id == Seat.id).filter(
        Seat.seat_number.like("EXAM-%"),
        Reservation.date >= start_date,
        Reservation.date <= end_date,
    ).first() is not None


def pick_reservation_time(exam_month: bool):
    if exam_month:
        block = weighted_choice([
            ((8, 11), 24),
            ((14, 17), 25),
            ((18, 22), 51),
        ])
    else:
        block = weighted_choice([
            ((8, 11), 28),
            ((14, 17), 36),
            ((18, 22), 36),
        ])
    start_hour = random.randint(block[0], block[1] - 2)
    duration = random.choice([2, 2, 3, 4])
    end_hour = min(start_hour + duration, block[1])
    return time(start_hour, 0), time(end_hour, 0)


def pick_reservation_date(month: date, exam_month: bool):
    picked = random_day(month)
    if exam_month and random.random() < 0.42:
        weekend_days = [
            date(month.year, month.month, day)
            for day in range(1, monthrange(month.year, month.month)[1] + 1)
            if date(month.year, month.month, day).weekday() >= 5
        ]
        if weekend_days:
            picked = random.choice(weekend_days)
    return picked


def create_reservations_for_month(
    month: date,
    exam_month: bool,
    students,
    teachers,
    power_seats,
    non_power_seats,
    stats: SeedStats,
):
    start_date, end_date, start_at, _ = month_range(month)
    if month_has_demo_reservations(start_date, end_date):
        stats.skipped_month_blocks += 1
        return

    reservation_count = 360 if exam_month else random.randint(190, 225)
    for _ in range(reservation_count):
        user = select_active_user(students, teachers, exam_month)
        with_power = random.random() < (0.66 if exam_month else 0.48)
        seat = random.choice(power_seats if with_power else non_power_seats)
        reservation_date = pick_reservation_date(month, exam_month)
        start_time, end_time = pick_reservation_time(exam_month)

        if exam_month:
            status = weighted_choice([
                ("completed", 64),
                ("checked_in", 18),
                ("reserved", 10),
                ("no_show", 5),
                ("cancelled", 3),
            ])
        else:
            status = weighted_choice([
                ("completed", 55),
                ("checked_in", 15),
                ("reserved", 12),
                ("no_show", 8),
                ("cancelled", 10),
            ])

        create_time = datetime.combine(reservation_date, time(max(start_time.hour - 3, 7), 0))
        checkin_time = None
        if status in ("checked_in", "completed"):
            checkin_time = datetime.combine(reservation_date, start_time) + timedelta(
                minutes=random.randint(-10, 18)
            )

        reservation = Reservation(
            user_id=user.id,
            seat_id=seat.id,
            date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
            checkin_time=checkin_time,
            create_time=create_time,
        )
        db.session.add(reservation)
        stats.reservations += 1


def month_has_demo_requests(start_at: datetime, end_at: datetime) -> bool:
    return BookRequest.query.filter(
        BookRequest.reason.like(f"{DEMO_MARK}%"),
        BookRequest.create_time >= start_at,
        BookRequest.create_time <= end_at,
    ).first() is not None


def create_book_requests_for_month(month: date, exam_month: bool, students, teachers, admin_id, stats: SeedStats):
    _, _, start_at, end_at = month_range(month)
    if month_has_demo_requests(start_at, end_at):
        stats.skipped_month_blocks += 1
        return

    request_count = 18 if exam_month else 5
    for index in range(request_count):
        title, author, reason = BOOK_REQUEST_TITLES[index % len(BOOK_REQUEST_TITLES)]
        user = select_active_user(students, teachers, exam_month)
        create_at = random_datetime(month, 10, 20)
        status = weighted_choice([
            ("pending", 35),
            ("approved", 45),
            ("rejected", 20),
        ])
        request_row = BookRequest(
            user_id=user.id,
            title=title,
            author=author,
            publisher=random.choice(["高等教育出版社", "电子工业出版社", "清华大学出版社", "人民邮电出版社"]),
            isbn=f"DEMO-REQ-{month_label(month)}-{index + 1:03d}",
            reason=f"{DEMO_MARK} {reason}",
            status=status,
            review_admin_id=admin_id if status != "pending" else None,
            review_comment="考试月演示数据：根据馆藏与预算评估处理。" if status != "pending" else None,
            create_time=create_at,
            update_time=create_at + timedelta(days=random.randint(0, 3)),
        )
        db.session.add(request_row)
        stats.book_requests += 1


def month_has_demo_repairs(start_at: datetime, end_at: datetime) -> bool:
    return SeatRepair.query.filter(
        SeatRepair.description.like(f"{DEMO_MARK}%"),
        SeatRepair.create_time >= start_at,
        SeatRepair.create_time <= end_at,
    ).first() is not None


def create_repairs_for_month(month: date, exam_month: bool, students, seats, admin_id, stats: SeedStats):
    _, _, start_at, end_at = month_range(month)
    if month_has_demo_repairs(start_at, end_at):
        stats.skipped_month_blocks += 1
        return

    repair_count = 12 if exam_month else 4
    for index in range(repair_count):
        user = random.choice(students[:42])
        seat = random.choice(seats)
        create_at = random_datetime(month, 8, 21)
        status = weighted_choice([
            ("pending", 28),
            ("fixing", 22),
            ("resolved", 42),
            ("rejected", 8),
        ])
        repair = SeatRepair(
            user_id=user.id,
            seat_id=seat.id,
            description=f"{DEMO_MARK} {REPAIR_DESCRIPTIONS[index % len(REPAIR_DESCRIPTIONS)]}",
            status=status,
            review_admin_id=admin_id if status != "pending" else None,
            review_comment="考试月座位高频使用，已安排巡检处理。" if status != "pending" else None,
            create_time=create_at,
            update_time=create_at + timedelta(days=random.randint(0, 4)),
        )
        db.session.add(repair)
        stats.repairs += 1


def month_has_demo_notifications(start_at: datetime, end_at: datetime) -> bool:
    return Notification.query.filter(
        Notification.content.like(f"{DEMO_MARK}%"),
        Notification.create_time >= start_at,
        Notification.create_time <= end_at,
    ).first() is not None


def create_notifications_for_month(month: date, exam_month: bool, students, teachers, stats: SeedStats):
    _, _, start_at, end_at = month_range(month)
    if month_has_demo_notifications(start_at, end_at):
        stats.skipped_month_blocks += 1
        return

    notification_count = 40 if exam_month else 12
    for _ in range(notification_count):
        title, type_name, content = random.choice(NOTIFICATION_TEMPLATES)
        user = select_active_user(students, teachers, exam_month)
        create_at = random_datetime(month, 8, 22)
        notification = Notification(
            user_id=user.id,
            title=title,
            content=f"{DEMO_MARK} {content}",
            type=type_name,
            is_read=random.random() < 0.64,
            create_time=create_at,
        )
        db.session.add(notification)
        stats.notifications += 1


def get_existing_admin_id():
    admin = User.query.filter_by(role="admin").order_by(User.id.asc()).first()
    return admin.id if admin else None


def build_seed_data(exam_month: date) -> SeedStats:
    random.seed(RANDOM_SEED + exam_month.year * 100 + exam_month.month)
    stats = SeedStats()

    category_map = {name: get_or_create_category(name, stats) for name in CATEGORIES}
    students, teachers = create_users(stats)
    db.session.flush()

    books_by_category, hot_books = create_books(category_map, stats)
    seats, power_seats, non_power_seats = create_seats(stats)
    db.session.flush()

    admin_id = get_existing_admin_id()
    months = [add_months(exam_month, -2), add_months(exam_month, -1), exam_month]

    for item in months:
        is_exam_month = item == exam_month
        create_borrows_for_month(item, is_exam_month, students, teachers, books_by_category, hot_books, stats)
        if is_exam_month:
            ensure_exam_month_hot_book_topup(item, students, hot_books, admin_id, stats)
        create_reservations_for_month(item, is_exam_month, students, teachers, power_seats, non_power_seats, stats)
        create_book_requests_for_month(item, is_exam_month, students, teachers, admin_id, stats)
        create_repairs_for_month(item, is_exam_month, students, seats, admin_id, stats)
        create_notifications_for_month(item, is_exam_month, students, teachers, stats)

    return stats


def print_report(stats: SeedStats, exam_month: date, dry_run: bool):
    mode = "DRY-RUN 预览（未写入数据库）" if dry_run else "实际写入完成"
    print("=" * 72)
    print(f"考试月演示数据脚本 - {mode}")
    print(f"考试月: {month_label(exam_month)}")
    print(f"生成范围: {month_label(add_months(exam_month, -2))} ~ {month_label(exam_month)}")
    print("-" * 72)
    for line in stats.as_lines():
        print(line)
    print("-" * 72)
    print("考试月特征：专业书借阅集中、热门专业书低库存、自习预约高峰偏晚间/周末、带电源座位偏好增强。")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="生成智慧图书馆考试月演示数据")
    parser.add_argument(
        "--month",
        type=parse_month,
        default=previous_month(),
        help="指定考试月，格式 YYYY-MM；默认使用当前日期的上个月",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览将生成的数据并回滚，不写入数据库",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        stats = build_seed_data(args.month)
        if args.dry_run:
            db.session.rollback()
        else:
            db.session.commit()
        print_report(stats, args.month, args.dry_run)


if __name__ == "__main__":
    main()
