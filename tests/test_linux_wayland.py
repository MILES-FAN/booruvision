import pytest

pytest.importorskip("dbus_next")

from dbus_next import introspection as intr  # noqa: E402

from booruvision.hotkeys.linux_wayland import SHORTCUTS_IFACE, shortcuts_only  # noqa: E402

PORTAL_XML = """<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="org.freedesktop.portal.PowerProfileMonitor">
    <property type="b" name="power-saver-enabled" access="read"/>
  </interface>
  <interface name="org.freedesktop.portal.GlobalShortcuts">
    <method name="CreateSession">
      <arg type="a{sv}" name="options" direction="in"/>
      <arg type="o" name="handle" direction="out"/>
    </method>
    <signal name="Activated">
      <arg type="o" name="session_handle"/>
      <arg type="s" name="shortcut_id"/>
      <arg type="t" name="timestamp"/>
      <arg type="a{sv}" name="options"/>
    </signal>
  </interface>
  <node name="request"/>
</node>"""


def test_full_portal_introspection_is_rejected_by_dbus_next():
    # The reason for shortcuts_only: a hyphenated property name fails the whole document
    with pytest.raises(Exception, match="power-saver-enabled"):
        intr.Node.parse(PORTAL_XML)


def test_shortcuts_only_keeps_just_the_global_shortcuts_interface():
    node = intr.Node.parse(shortcuts_only(PORTAL_XML))
    assert [i.name for i in node.interfaces] == [SHORTCUTS_IFACE]
    interface = node.interfaces[0]
    assert [m.name for m in interface.methods] == ["CreateSession"]
    assert [s.name for s in interface.signals] == ["Activated"]


def test_shortcuts_only_without_support_has_no_interfaces():
    xml = '<node><interface name="org.freedesktop.portal.Settings"/></node>'
    assert intr.Node.parse(shortcuts_only(xml)).interfaces == []
