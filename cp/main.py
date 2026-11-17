    sim = CyberGameOfLife(size=50, p=0.25, seed=42)
    current_theme = ["Неон-лайм"]
    is_drawing = [False]
    draw_button = [1]
    last_cell = [None]
    plot_bounds = [25, 250]

    fig = plt.figure(figsize=(13.5, 7.2), facecolor="#0b0b0d")
    fig.canvas.manager.set_window_title("Conway's Game of Life — Cyber Edition")

    # Ігрове поле
    ax_grid = fig.add_axes([0.03, 0.25, 0.41, 0.68])
    ax_grid.set_facecolor("#08080a")
    for spine in ax_grid.spines.values():
        spine.set_edgecolor("#00ff41")
        spine.set_linewidth(1.2)

    img = ax_grid.imshow(sim.trail_grid, cmap=CACHED_CMAPS[current_theme[0]], vmin=0, vmax=1, animated=True)
    ax_grid.set_xticks([])
    ax_grid.set_yticks([])

    hud_text = ax_grid.text(
        0.02, 0.98, "", transform=ax_grid.transAxes,
        fontsize=9, color="#ffffff", va="top", ha="left", animated=True,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#0b0b0d", edgecolor="#333340", alpha=0.82)
    )

    # Графік метрик
    ax_plot = fig.add_axes([0.49, 0.43, 0.48, 0.50])
    ax_plot.set_facecolor("#111115")
    ax_plot.set_xlim(0, plot_bounds[0])
    ax_plot.set_ylim(0, plot_bounds[1])
    line_alive, = ax_plot.plot([], [], color="#00ff41", lw=2, label="Живі клітини A(t)", animated=True)
    line_diff, = ax_plot.plot([], [], color="#ff007f", lw=1.4, linestyle="--", label="Активність змін за крок", animated=True)
    ax_plot.set_xlabel("Покоління (t)", color="#a0a0b0")
    ax_plot.set_ylabel("Кількість клітин", color="#a0a0b0")
    ax_plot.grid(True, linestyle=":", color="#2a2a35", alpha=0.8)
    ax_plot.legend(loc="upper right", fontsize=9, facecolor="#181820", edgecolor="#333340")

    # Кнопки
    btn_specs = [
        ([0.03, 0.14, 0.09, 0.055], "Пауза"),
        ([0.13, 0.14, 0.09, 0.055], "+1 Крок"),
        ([0.23, 0.14, 0.09, 0.055], "Скинути"),
        ([0.33, 0.14, 0.11, 0.055], "Очистити"),
        ([0.85, 0.04, 0.12, 0.055], "Зберегти CSV"),
    ]
    buttons = []
    for rect, label in btn_specs:
        b = Button(fig.add_axes(rect), label, color="#1a1a22", hovercolor="#2c2c3a")
        b.label.set_color("#ffffff")
        b.label.set_fontsize(9.5)
        buttons.append(b)
    btn_pause, btn_step, btn_reset, btn_clear, btn_save = buttons

    # Повзунок швидкості
    ax_speed = fig.add_axes([0.11, 0.055, 0.33, 0.035])
    ax_speed.set_facecolor("#1a1a22")
    slider_speed = Slider(ax_speed, "Затримка (мс)", 20, 400, valinit=60, valstep=10, color="#00ff41")
    slider_speed.label.set_color("#cccccc")
    slider_speed.valtext.set_color("#00ff41")

    # Перемикачі налаштувань
    ax_color = fig.add_axes([0.49, 0.04, 0.12, 0.28])
    style_widget_box(ax_color, "Колір кубиків")
    radio_color = RadioButtons(ax_color, tuple(COLOR_SPECS.keys()), activecolor="#00ff41")

    ax_brush = fig.add_axes([0.62, 0.17, 0.11, 0.15])
    style_widget_box(ax_brush, "Пензель (ЛКМ)")
    radio_brush = RadioButtons(ax_brush, ("1 Кубик", "Глайдер", "Хаос-бомба"), activecolor="#00ff41")

    ax_bound = fig.add_axes([0.62, 0.04, 0.11, 0.10])
    style_widget_box(ax_bound, "Межі поля")
    radio_bound = RadioButtons(ax_bound, ("Тор", "Стіни"), activecolor="#00ff41")

    ax_rules = fig.add_axes([0.74, 0.17, 0.11, 0.15])
    style_widget_box(ax_rules, "Правила")
    radio_rules = RadioButtons(ax_rules, ("Conway (B3/S23)", "HighLife (B36/S23)", "Seeds (B2/S)"), activecolor="#00ff41")

    ax_presets = fig.add_axes([0.86, 0.12, 0.11, 0.20])
    style_widget_box(ax_presets, "Шаблони")
    radio_presets = RadioButtons(ax_presets, ("Випадково", "Глайдерна гармата", "Корабель LWSS", "Пульсар (T=3)"), activecolor="#00ff41")

    for r_group in (radio_color, radio_brush, radio_bound, radio_rules, radio_presets):
        for lbl in r_group.labels:
            lbl.set_color("#e0e0ec")
            lbl.set_fontsize(8.5)

    def sync_artists(force_full_redraw=False):
        if current_theme[0] == "Вік клітин":
            img.set_data(sim.age_grid)
        else:
            img.set_data(sim.trail_grid)

        line_alive.set_data(sim.gens, sim.alives)
        line_diff.set_data(sim.gens, sim.changes)

        need_rescale = False
        if sim.generation + 2 > plot_bounds[0]:
            plot_bounds[0] = int((sim.generation + 2) * 1.4)
            ax_plot.set_xlim(0, plot_bounds[0])
            need_rescale = True

        cur_max = max(sim.alives[-1], sim.changes[-1])
        if cur_max * 1.1 > plot_bounds[1]:
            plot_bounds[1] = int(cur_max * 1.35)
            ax_plot.set_ylim(0, plot_bounds[1])
            need_rescale = True

        density = sim.history[-1][4]
        status = f"Стабілізація: t={sim.stabilized_at}" if sim.stabilized_at else ("ПАУЗА" if sim.paused else "АКТИВНО")
        hud_text.set_text(f"t={sim.generation} | Живих: {sim.alives[-1]} (ρ={density}) | {status}")

        if force_full_redraw or need_rescale:
            fig.canvas.draw_idle()

    def toggle_pause(event):
        sim.paused = not sim.paused
        btn_pause.label.set_text("Старт" if sim.paused else "Пауза")
        sync_artists(force_full_redraw=True)

    def do_step(event):
        sim.paused = True
        btn_pause.label.set_text("Старт")
        sim.step()
        sync_artists(force_full_redraw=True)

    def do_reset(event):
        plot_bounds[:] = [25, 250]
        ax_plot.set_xlim(0, plot_bounds[0])
        ax_plot.set_ylim(0, plot_bounds[1])
        sim.apply_preset(sim.preset_name)
        sync_artists(force_full_redraw=True)

    def do_clear(event):
        sim.paused = True
        btn_pause.label.set_text("Старт")
        plot_bounds[:] = [25, 100]
        ax_plot.set_xlim(0, plot_bounds[0])
        ax_plot.set_ylim(0, plot_bounds[1])
        sim.apply_preset("Порожнє поле")
        sync_artists(force_full_redraw=True)

    def do_save(event):
        sim.export_csv("simulation_history.csv")

    def change_color(label):
        current_theme[0] = label
        img.set_cmap(CACHED_CMAPS[label])
        img.set_clim(0, 15 if label == "Вік клітин" else 1)

        accent = "#00f3ff" if label == "Вік клітин" else COLOR_SPECS[label][-1]
        line_alive.set_color(accent)
        for spine in ax_grid.spines.values():
            spine.set_edgecolor(accent)
        sync_artists(force_full_redraw=True)

    def change_brush(label):
        sim.brush_mode = label

    def change_rule(label):
        sim.rule_name = label

    def change_bound(label):
        sim.boundary = label

    def change_preset(label):
        plot_bounds[:] = [25, 250]
        ax_plot.set_xlim(0, plot_bounds[0])
        ax_plot.set_ylim(0, plot_bounds[1])
        sim.apply_preset(label)
        sync_artists(force_full_redraw=True)

    def handle_paint(event):
        if event.inaxes == ax_grid and event.xdata is not None and event.ydata is not None:
            col = int(round(event.xdata))
            row = int(round(event.ydata))
            if 0 <= row < sim.size and 0 <= col < sim.size:
                if last_cell[0] == (row, col, draw_button[0]):
                    return
                last_cell[0] = (row, col, draw_button[0])
                sim.apply_brush(row, col, erase=(draw_button[0] == 3))
                sim._record_metrics(born=0, died=0)
                sync_artists(force_full_redraw=True)

    def on_press(event):
        if event.inaxes == ax_grid:
            is_drawing[0] = True
            draw_button[0] = event.button
            last_cell[0] = None
            handle_paint(event)

    def on_motion(event):
        if is_drawing[0]:
            handle_paint(event)

    def on_release(event):
        is_drawing[0] = False
        last_cell[0] = None

    btn_pause.on_clicked(toggle_pause)
    btn_step.on_clicked(do_step)
    btn_reset.on_clicked(do_reset)
    btn_clear.on_clicked(do_clear)
    btn_save.on_clicked(do_save)
    radio_color.on_clicked(change_color)
    radio_brush.on_clicked(change_brush)
    radio_rules.on_clicked(change_rule)
    radio_bound.on_clicked(change_bound)
    radio_presets.on_clicked(change_preset)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    def update(frame):
        if not sim.paused:
            sim.step()
            sync_artists(force_full_redraw=False)
        return (img, line_alive, line_diff, hud_text)

    sync_artists(force_full_redraw=True)
    anim = FuncAnimation(fig, update, interval=60, blit=True, cache_frame_data=False)

    def change_speed(val):
        anim.event_source.interval = int(val)

    slider_speed.on_changed(change_speed)
    plt.show()
