#include "guard.h"

#include <QQmlExtensionPlugin>
#include <qqml.h>

class DotfilesContextGuardPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)

public:
    void registerTypes(const char *uri) override {
        qmlRegisterType<ContextMenuGuard>(uri, 1, 0, "ContextMenuGuard");
    }
};

#include "plugin.moc"
