#include <QContextMenuEvent>
#include <QCoreApplication>
#include <QEvent>
#include <QEventLoop>
#include <QGuiApplication>
#include <QObject>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QUrl>
#include <QVariant>

#include <iostream>
#include <memory>
#include <string>

namespace {

int fail(const std::string &message) {
    std::cerr << "FAIL: " << message << std::endl;
    return 1;
}

class EventRecorder final : public QObject {
public:
    bool armed = false;
    int contextMenus = 0;
    int userEvents = 0;

    void reset() {
        contextMenus = 0;
        userEvents = 0;
    }

protected:
    bool eventFilter(QObject *, QEvent *event) override {
        if (!armed)
            return false;
        if (event->type() == QEvent::ContextMenu) {
            ++contextMenus;
            return true;
        }
        if (event->type() == QEvent::User) {
            ++userEvents;
            return true;
        }
        return false;
    }
};

void dispatchContextMenu(QObject *target, const QPoint &position) {
    QContextMenuEvent event(QContextMenuEvent::Mouse, position, position);
    QCoreApplication::sendEvent(target, &event);
}

std::unique_ptr<QObject> loadGuard(QQmlEngine &engine) {
    QQmlComponent component(&engine);
    component.setData("import Dotfiles.ContextMenuGuard 1.0\nContextMenuGuard {}\n", QUrl());
    if (component.isError()) {
        std::cerr << "GUARD_LOAD_FAILED: " << component.errorString().toStdString();
        return nullptr;
    }
    std::unique_ptr<QObject> guard(component.create());
    if (!guard) {
        std::cerr << "GUARD_LOAD_FAILED: " << component.errorString().toStdString();
        return nullptr;
    }
    QQmlEngine::setObjectOwnership(guard.get(), QQmlEngine::CppOwnership);
    const QVariant active = guard->property("active");
    if (!active.isValid() || !active.toBool()) {
        std::cerr << "GUARD_INACTIVE: the actual QML extension did not report activation\n";
        return nullptr;
    }
    return guard;
}

} // namespace

int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    if (argc != 2)
        return fail("usage: omarchy-context-menu baseline|guarded|controls");
    const std::string mode(argv[1]);
    if (mode != "baseline" && mode != "guarded" && mode != "controls")
        return fail("unknown mode");

    QQuickWindow focuslessWindow;
    if (focuslessWindow.activeFocusItem() != nullptr)
        return fail("baseline window unexpectedly has an active focus item");

    if (mode == "baseline") {
        std::cout << "BASELINE: delivering a real origin context-menu event without a guard" << std::endl;
        dispatchContextMenu(&focuslessWindow, QPoint(0, 0));
        std::cout << "BASELINE_SURVIVED" << std::endl;
        return 0;
    }

    // Application filters run in reverse installation order. The actual native
    // guard must see controls first; this recorder safely receives forwarded
    // events without letting an intentionally unguarded event reach Qt's bug.
    EventRecorder recorder;
    if (mode == "controls")
        app.installEventFilter(&recorder);
    QQmlEngine engine;
    auto guard = loadGuard(engine);
    if (!guard)
        return 2;

    if (mode == "guarded") {
        // No recorder protects this path: survival exercises the real guard
        // against exactly the Qt delivery path used by the crashing baseline.
        dispatchContextMenu(&focuslessWindow, QPoint(0, 0));
        std::cout << "PASS: guarded origin event survived real Qt delivery" << std::endl;
        return 0;
    }

    recorder.armed = true;
    dispatchContextMenu(&focuslessWindow, QPoint(0, 0));
    if (recorder.contextMenus != 0)
        return fail("the unsafe origin event reached the fallback recorder");
    std::cout << "PASS: focusless origin consumed" << std::endl;

    recorder.reset();
    dispatchContextMenu(&focuslessWindow, QPoint(7, 9));
    if (recorder.contextMenus != 1)
        return fail("a non-origin context menu was suppressed");
    std::cout << "PASS: non-origin context menu forwarded" << std::endl;

    QQuickWindow focusedWindow;
    QQuickItem focusedItem(focusedWindow.contentItem());
    focusedItem.setSize(QSizeF(20, 20));
    focusedWindow.show();
    focusedWindow.requestActivate();
    focusedItem.forceActiveFocus(Qt::OtherFocusReason);
    QCoreApplication::processEvents(QEventLoop::AllEvents);
    focusedItem.forceActiveFocus(Qt::OtherFocusReason);
    if (focusedWindow.activeFocusItem() == nullptr) {
        std::cerr << "FOCUS_CONTROL_UNAVAILABLE: this platform did not activate the isolated window\n";
        return 77;
    }
    recorder.reset();
    dispatchContextMenu(&focusedWindow, QPoint(0, 0));
    if (recorder.contextMenus != 1)
        return fail("a focused origin context menu was suppressed");
    std::cout << "PASS: focused origin context menu forwarded" << std::endl;

    QObject ordinaryObject;
    recorder.reset();
    dispatchContextMenu(&ordinaryObject, QPoint(0, 0));
    if (recorder.contextMenus != 1)
        return fail("a non-window context menu was suppressed");
    std::cout << "PASS: non-window context menu forwarded" << std::endl;

    recorder.reset();
    QEvent ordinaryEvent(QEvent::User);
    QCoreApplication::sendEvent(&focuslessWindow, &ordinaryEvent);
    if (recorder.userEvents != 1)
        return fail("an unrelated event was suppressed");
    std::cout << "PASS: unrelated event forwarded" << std::endl;

    guard.reset();
    engine.collectGarbage();
    recorder.reset();
    dispatchContextMenu(&focuslessWindow, QPoint(0, 0));
    if (recorder.contextMenus != 1)
        return fail("the native filter outlived its service-owned object");
    std::cout << "PASS: destroying the guard removed its native filter" << std::endl;
    app.removeEventFilter(&recorder);
    return 0;
}
