import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


# =================================
# DATABASE CLASS (SQLite)
# =================================
class Database:

    def __init__(self, db_name="todostudy.db"):
        self.db_name = db_name
        self.create_table()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS homeworks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    deadline TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def add_homework(self, subject, detail, deadline):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO homeworks (subject, detail, deadline, status)
                VALUES (?, ?, ?, ?)
            """,
                (subject, detail, deadline, "Not Completed"),
            )
            conn.commit()

    def get_all_homeworks(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, subject, detail, deadline, status FROM homeworks"
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "subject": row[1],
                    "detail": row[2],
                    "deadline": row[3],
                    "status": row[4],
                }
                for row in rows
            ]

    def update_status(self, hw_id, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE homeworks SET status = ? WHERE id = ?", (status, hw_id)
            )
            conn.commit()

    def delete_homework(self, hw_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM homeworks WHERE id = ?", (hw_id,))
            conn.commit()


# =================================
# CUSTOM WIDGETS
# =================================
class ColorfulButton(Button):

    def __init__(
        self,
        bg_color=(0.15, 0.45, 0.95, 1),
        text_color=(1, 1, 1, 1),
        radius=14,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = text_color
        self.bold = True

        with self.canvas.before:
            self.rect_color = Color(*bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[radius]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CardWidget(BoxLayout):

    def __init__(
        self,
        bg_color=(0.1, 0.14, 0.22, 0.95),
        border_color=(0.2, 0.3, 0.45, 1),
        radius=16,
        **kwargs,
    ):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*border_color)
            self.border_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[radius]
            )
            Color(*bg_color)
            self.bg_rect = RoundedRectangle(
                pos=(self.pos[0] + 1, self.pos[1] + 1),
                size=(max(0, self.size[0] - 2), max(0, self.size[1] - 2)),
                radius=[radius],
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.pos[0] + 1, self.pos[1] + 1)
        self.bg_rect.size = (
            max(0, self.size[0] - 2),
            max(0, self.size[1] - 2),
        )


# =================================
# MAIN APP CLASS (ToDo Study)
# =================================
class ToDoStudy(App):

    def build(self):
        self.db = Database()
        self.current_view_popup = None
        self.search_query = ""

        main = BoxLayout(orientation="vertical", padding=30, spacing=12)

        with main.canvas.before:
            Color(0.05, 0.07, 0.13, 1)
            self.background = RoundedRectangle(pos=main.pos, size=main.size)

        main.bind(pos=self.update_background, size=self.update_background)

        # ดันเนื้อหาจากด้านบนลงมากึ่งกลาง
        main.add_widget(Widget(size_hint_y=1))

        # Header Title
        title_box = BoxLayout(
            orientation="vertical", size_hint_y=None, height=90, spacing=5
        )

        title = Label(
            text="=== TODO STUDY ===",
            font_size=36,
            bold=True,
            color=(0.35, 0.75, 1, 1),
        )

        subtitle = Label(
            text="Your Personal Smart Homework Assistant",
            font_size=15,
            color=(0.7, 0.8, 0.95, 0.8),
        )

        title_box.add_widget(title)
        title_box.add_widget(subtitle)
        main.add_widget(title_box)

        # Space ระหว่าง Title กับปุ่ม
        main.add_widget(Widget(size_hint_y=None, height=15))

        # Main Menu Buttons
        add_button = ColorfulButton(
            text="+  ADD NEW HOMEWORK",
            bg_color=(0.2, 0.65, 0.95, 1),
            font_size=17,
            size_hint_y=None,
            height=58,
        )

        view_button = ColorfulButton(
            text="[ View Homework List ]",
            bg_color=(0.55, 0.3, 0.95, 1),
            font_size=17,
            size_hint_y=None,
            height=58,
        )

        reminder_button = ColorfulButton(
            text="!  DEADLINE REMINDER",
            bg_color=(0.95, 0.45, 0.2, 1),
            font_size=17,
            size_hint_y=None,
            height=58,
        )

        add_button.bind(on_press=self.add_homework)
        view_button.bind(on_press=lambda x: self.view_homework(keep_search=False))
        reminder_button.bind(on_press=self.deadline_reminder)

        main.add_widget(add_button)
        main.add_widget(view_button)
        main.add_widget(reminder_button)

        # ข้อความสโลแกนด้านล่าง
        main.add_widget(
            Label(
                text="Turn your deadlines into accomplishments!",
                font_size=13,
                color=(0.4, 0.6, 0.7, 0.8),
                size_hint_y=None,
                height=35,
            )
        )

        # ดันเนื้อหาจากด้านล่างขึ้นมากึ่งกลาง
        main.add_widget(Widget(size_hint_y=1))

        return main

    def update_background(self, *args):
        self.background.pos = args[0].pos
        self.background.size = args[0].size

    def days_remaining(self, deadline_str):
        try:
            deadline_date = datetime.strptime(
                deadline_str, "%d/%m/%Y"
            ).date()
            today = datetime.now().date()
            return (deadline_date - today).days
        except ValueError:
            return 0

    def show_message(self, message):
        layout = CardWidget(
            orientation="vertical",
            padding=20,
            spacing=15,
            bg_color=(0.08, 0.12, 0.2, 1),
            border_color=(0.3, 0.5, 0.8, 1),
        )

        lbl = Label(
            text=message,
            font_size=16,
            halign="center",
            valign="center",
            color=(0.9, 0.95, 1, 1),
        )
        lbl.bind(size=lbl.setter("text_size"))
        layout.add_widget(lbl)

        close = ColorfulButton(
            text="OK",
            bg_color=(0.2, 0.6, 0.9, 1),
            size_hint_y=None,
            height=45,
        )
        layout.add_widget(close)

        popup = Popup(
            title="Notification", content=layout, size_hint=(0.85, 0.35)
        )
        close.bind(on_press=popup.dismiss)
        popup.open()

    # =================================
    # ADD HOMEWORK
    # =================================
    def add_homework(self, instance):
        layout = CardWidget(
            orientation="vertical",
            padding=20,
            spacing=12,
            bg_color=(0.08, 0.12, 0.2, 1),
            border_color=(0.2, 0.65, 0.95, 1),
        )

        title = Label(
            text="ADD NEW HOMEWORK",
            font_size=20,
            bold=True,
            color=(0.35, 0.75, 1, 1),
            size_hint_y=None,
            height=35,
        )

        subject = TextInput(
            hint_text="Subject (e.g. Mathematics)",
            multiline=False,
            font_size=16,
            background_color=(0.15, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.35, 0.75, 1, 1),
        )

        detail = TextInput(
            hint_text="Homework Details",
            multiline=False,
            font_size=16,
            background_color=(0.15, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.35, 0.75, 1, 1),
        )

        deadline = TextInput(
            hint_text="Deadline (DD/MM/YYYY)",
            multiline=False,
            font_size=16,
            background_color=(0.15, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.35, 0.75, 1, 1),
        )

        save = ColorfulButton(
            text="Save Homework",
            bg_color=(0.15, 0.75, 0.45, 1),
            size_hint_y=None,
            height=45,
            
        )

        layout.add_widget(title)
        layout.add_widget(subject)
        layout.add_widget(detail)
        layout.add_widget(deadline)
        layout.add_widget(save)

        popup = Popup(
            title="ToDo Study System", content=layout, size_hint=(0.9, 0.75)
        )

        save.bind(
            on_press=lambda x: self.save_homework(
                subject.text, detail.text, deadline.text, popup
            )
        )
        popup.open()

    # =================================
    # SAVE
    # =================================
    def save_homework(self, subject, detail, deadline, popup):
        if not subject.strip() or not detail.strip() or not deadline.strip():
            self.show_message("Please fill in all fields.")
            return

        try:
            datetime.strptime(deadline.strip(), "%d/%m/%Y")
        except ValueError:
            self.show_message("Invalid date format.\nUse DD/MM/YYYY")
            return

        self.db.add_homework(subject.strip(), detail.strip(), deadline.strip())
        popup.dismiss()
        self.show_message("Homework added successfully!")

    # =================================
    # VIEW HOMEWORK (WITH STATISTICS & SEARCH)
    # =================================
    def view_homework(self, instance=None, keep_search=False):
        if not keep_search:
            self.search_query = ""

        main_layout = BoxLayout(
            orientation="vertical", padding=15, spacing=10
        )

        # ดึงข้อมูลการบ้านทั้งหมด
        all_homeworks = self.db.get_all_homeworks()

        # คำนวณสถิติรวมทั้งหมด
        total_count = len(all_homeworks)
        completed_count = sum(1 for hw in all_homeworks if hw["status"] == "Completed")
        not_completed_count = total_count - completed_count

        # ---------------------------------
        # แถบแสดงสถิติ (Statistics Card)
        # ---------------------------------
        stats_card = CardWidget(
            orientation="horizontal",
            padding=10,
            spacing=10,
            size_hint_y=None,
            height=55,
            bg_color=(0.06, 0.1, 0.17, 0.95),
            border_color=(0.25, 0.45, 0.7, 1),
        )

        stats_text = (
            f"[b]Total:[/b] {total_count}   |   "
            f"[color=55ff77][b]Completed:[/b] {completed_count}[/color]   |   "
            f"[color=ff9944][b]Not Completed:[/b] {not_completed_count}[/color]"
        )

        stats_label = Label(
            text=stats_text,
            markup=True,
            font_size=15,
            halign="center",
            valign="center",
        )
        stats_label.bind(size=stats_label.setter("text_size"))
        stats_card.add_widget(stats_label)

        main_layout.add_widget(stats_card)

        # ---------------------------------
        # ช่องค้นหา (Search Input)
        # ---------------------------------
        search_input = TextInput(
            text=self.search_query,
            hint_text="Search by subject name...",
            multiline=False,
            size_hint_y=None,
            height=45,
            font_size=16,
            background_color=(0.15, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.35, 0.75, 1, 1),
        )

        search_input.bind(text=self.on_search_change)
        main_layout.add_widget(search_input)

        # กรองข้อมูลตามคำค้นหา
        if self.search_query.strip():
            homeworks = [
                hw
                for hw in all_homeworks
                if self.search_query.lower() in hw["subject"].lower()
            ]
        else:
            homeworks = all_homeworks

        # ---------------------------------
        # รายการการบ้าน (Homework List)
        # ---------------------------------
        if not homeworks:
            msg = (
                "No homework matches your search."
                if self.search_query
                else "No homework recorded yet."
            )
            main_layout.add_widget(
                Label(text=msg, font_size=18, color=(0.7, 0.8, 0.9, 1))
            )
        else:
            scroll = ScrollView()
            content_layout = BoxLayout(
                orientation="vertical", spacing=15, size_hint_y=None
            )
            content_layout.bind(
                minimum_height=content_layout.setter("height")
            )

            for i, hw in enumerate(homeworks):
                days = self.days_remaining(hw["deadline"])
                is_completed = hw["status"] == "Completed"

                card_bg = (
                    (0.08, 0.18, 0.12, 0.95)
                    if is_completed
                    else (0.09, 0.14, 0.24, 0.95)
                )
                card_border = (
                    (0.2, 0.7, 0.4, 1) if is_completed else (0.3, 0.5, 0.8, 1)
                )

                item_box = CardWidget(
                    orientation="vertical",
                    padding=15,
                    spacing=10,
                    size_hint_y=None,
                    height=180,
                    bg_color=card_bg,
                    border_color=card_border,
                )

                if is_completed:
                    days_text = "[DONE]"
                elif days < 0:
                    days_text = f"OVERDUE ({abs(days)} days ago)"
                elif days == 0:
                    days_text = "DUE TODAY!"
                else:
                    days_text = f"{days} day(s) left"

                status_mark = (
                    "[OK] COMPLETED" if is_completed else "[..] IN PROGRESS"
                )

                info_text = (
                    f"[b]{i + 1}. {hw['subject']}[/b]\n"
                    f"Detail: {hw['detail']}\n"
                    f"Deadline: {hw['deadline']} ({days_text})\n"
                    f"Status: {status_mark}"
                )

                info = Label(
                    text=info_text,
                    font_size=15,
                    markup=True,
                    halign="center",
                    valign="center",
                    size_hint_y=None,
                    height=100,
                    color=(
                        (0.7, 0.95, 0.75, 1)
                        if is_completed
                        else (0.9, 0.95, 1, 1)
                    ),
                )
                info.bind(size=info.setter("text_size"))
                item_box.add_widget(info)

                btn_box = BoxLayout(
                    orientation="horizontal",
                    spacing=10,
                    size_hint_y=None,
                    height=40,
                )

                hw_id = hw["id"]
                done_btn = ColorfulButton(
                    text="V  Done" if not is_completed else "Undo",
                    bg_color=(
                        (0.15, 0.7, 0.4, 1)
                        if not is_completed
                        else (0.4, 0.5, 0.6, 1)
                    ),
                    font_size=14,
                )
                delete_btn = ColorfulButton(
                    text="X  Delete",
                    bg_color=(0.9, 0.25, 0.3, 1),
                    font_size=14,
                )

                target_status = (
                    "Not Completed" if is_completed else "Completed"
                )
                done_btn.bind(
                    on_press=lambda x, id_num=hw_id,
                    st=target_status: self.mark_completed(id_num, st)
                )
                delete_btn.bind(
                    on_press=lambda x, id_num=hw_id: self.delete_homework(
                        id_num
                    )
                )

                btn_box.add_widget(done_btn)
                btn_box.add_widget(delete_btn)

                item_box.add_widget(btn_box)
                content_layout.add_widget(item_box)

            scroll.add_widget(content_layout)
            main_layout.add_widget(scroll)

        close = ColorfulButton(
            text="Close List",
            bg_color=(0.3, 0.4, 0.5, 1),
            size_hint_y=None,
            height=50,
        )
        main_layout.add_widget(close)

        if self.current_view_popup:
            self.current_view_popup.dismiss()

        self.current_view_popup = Popup(
            title="HOMEWORK DASHBOARD",
            content=main_layout,
            size_hint=(0.95, 0.9),
        )
        close.bind(on_press=self.current_view_popup.dismiss)
        self.current_view_popup.open()

    def on_search_change(self, instance, value):
        self.search_query = value
        self.view_homework(keep_search=True)

    # =================================
    # COMPLETE & DELETE
    # =================================
    def mark_completed(self, hw_id, status="Completed"):
        self.db.update_status(hw_id, status)
        self.view_homework(keep_search=True)

    def delete_homework(self, hw_id):
        self.db.delete_homework(hw_id)
        self.view_homework(keep_search=True)

    # =================================
    # REMINDER
    # =================================
    def deadline_reminder(self, instance):
        homeworks = self.db.get_all_homeworks()
        reminders = []

        for hw in homeworks:
            if hw["status"] == "Completed":
                continue

            days = self.days_remaining(hw["deadline"])

            if days < 0:
                reminders.append(f"[!] {hw['subject']} - OVERDUE!")
            elif days == 0:
                reminders.append(f"[!] {hw['subject']} - Due TODAY!")
            elif days <= 3:
                reminders.append(
                    f"[*] {hw['subject']} - {days} day(s) remaining"
                )

        message = (
            "\n".join(reminders)
            if reminders
            else "Great job! No urgent deadlines."
        )

        layout = CardWidget(orientation="vertical",
            padding=20,
            spacing=15,
            bg_color=(0.12, 0.08, 0.18, 1),
            border_color=(0.95, 0.45, 0.2, 1),
        )

        lbl = Label(
            text=message,
            font_size=17,
            halign="center",
            valign="center",
            color=(1, 0.9, 0.8, 1),
        )
        lbl.bind(size=lbl.setter("text_size"))
        layout.add_widget(lbl)

        close = ColorfulButton(
            text="Got it!",
            bg_color=(0.95, 0.45, 0.2, 1),
            size_hint_y=None,
            height=50,
        )
        layout.add_widget(close)

        popup = Popup(
            title="DEADLINE ALERTS", content=layout, size_hint=(0.9, 0.6)
        )
        close.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    ToDoStudy().run()


        
