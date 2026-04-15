import flet as ft

def main(page: ft.Page):
    fp = ft.FilePicker()
    page.overlay.append(fp)
    page.update()
    
    def on_click(e):
        print("Clicking")
        res = fp.pick_files()
        print(type(res))
        import asyncio
        if asyncio.iscoroutine(res):
            print("É coroutine")
        page.update()

    page.add(ft.ElevatedButton("Pick", on_click=on_click))

ft.run(main)
