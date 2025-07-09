from .monkeypatches._monkeypatch_stock_landed_cost import (
    _get_patchable_methods as _get_patchable_methods_stock_landed_cost,
)
from .monkeypatches._monkeypatch_stock_move import (
    _get_patchable_methods as _get_patchable_methods_stock_move,
)


def _patch_method(cls, method_name, func):
    origin_method_name = f"_origin_{method_name}"
    if hasattr(func, origin_method_name):
        return
    origin_method = getattr(cls, method_name)
    setattr(func, origin_method_name, origin_method)
    setattr(cls, method_name, func)


def _unpatch_method(cls, method_name, func):
    origin_method_name = f"_origin_{method_name}"
    if not hasattr(func, origin_method_name):
        return

    origin_method = getattr(func, origin_method_name)
    setattr(cls, method_name, origin_method)
    delattr(func, origin_method_name)


def _patch_methods():
    methods_list = _get_patchable_methods_stock_move()
    for method_struct in methods_list:
        _patch_method(
            method_struct["class"],
            method_struct["method_name"],
            method_struct["new_method"],
        )

    methods_list = _get_patchable_methods_stock_landed_cost()
    for method_struct in methods_list:
        _patch_method(
            method_struct["class"],
            method_struct["method_name"],
            method_struct["new_method"],
        )


def _unpatch_methods():
    methods_list = _get_patchable_methods_stock_move()
    for method_struct in methods_list:
        _unpatch_method(
            method_struct["class"],
            method_struct["method_name"],
            method_struct["new_method"],
        )

    methods_list = _get_patchable_methods_stock_landed_cost()
    for method_struct in methods_list:
        _unpatch_method(
            method_struct["class"],
            method_struct["method_name"],
            method_struct["new_method"],
        )


def post_init_hook(env):
    _patch_methods()


def post_load_hook():
    _patch_methods()


def uninstall_hook(env):
    _unpatch_methods()
