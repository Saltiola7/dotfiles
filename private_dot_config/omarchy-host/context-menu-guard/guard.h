#pragma once

#include <QContextMenuEvent>
#include <QCoreApplication>
#include <QDebug>
#include <QEvent>
#include <QObject>
#include <QPointer>
#include <QQuickWindow>

class ContextMenuGuard : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool active READ active CONSTANT)

public:
    explicit ContextMenuGuard(QObject *parent = nullptr)
        : QObject(parent), application_(QCoreApplication::instance()) {
        if (!application_ || application_->thread() != thread())
            return;
        application_->installEventFilter(this);
        installed_ = true;
        qInfo("OMARCHY_CONTEXT_MENU_GUARD_ACTIVE");
    }

    ~ContextMenuGuard() override {
        if (application_ && installed_)
            application_->removeEventFilter(this);
    }

    bool active() const { return application_ && installed_; }

protected:
    bool eventFilter(QObject *target, QEvent *event) override {
        if (event->type() != QEvent::ContextMenu)
            return false;
        auto *window = qobject_cast<QQuickWindow *>(target);
        if (!window)
            return false;
        auto *contextMenu = static_cast<QContextMenuEvent *>(event);
        // Qt treats the origin as a positionless event and dereferences the
        // active focus item. Focusless layer-shell windows have no such item.
        return contextMenu->pos().isNull() && window->activeFocusItem() == nullptr;
    }

private:
    QPointer<QCoreApplication> application_;
    bool installed_ = false;
};
