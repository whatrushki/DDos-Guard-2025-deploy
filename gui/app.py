import flet as ft

def main(page: ft.Page):
  page.title = "Hello, Flet"
  page.add(ft.Text("Git url:"))
  page.vertical_alignment = ft.MainAxisAlignment.CENTER
  page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
  txt_number = ft.TextField(value="", text_align="right", width=300)
  page.add(txt_number)

ft.app(target=main)
