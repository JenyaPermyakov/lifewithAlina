import os
from tempfile import NamedTemporaryFile, gettempdir

os.environ.setdefault("MPLCONFIGDIR", os.path.join(gettempdir(), "matplotlib"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def build_sleep_chart(records):
    dates = []
    hours = []

    for r in records:
        dates.append(r.created_at.strftime("%d.%m"))
        hours.append(r.duration / 60)

    fig, ax = plt.subplots()
    ax.plot(dates, hours, marker="o")
    ax.set_title("Сон за неделю")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Часы сна")
    ax.grid()
    fig.tight_layout()

    with NamedTemporaryFile(
        delete=False,
        suffix=".png",
        prefix="sleep_chart_",
    ) as chart_file:
        filename = chart_file.name

    fig.savefig(filename)
    plt.close(fig)

    return filename
