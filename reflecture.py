"""
Note that this file for use by PyBryt and should not be modified.
"""
import os
import sys
import pybryt


# --- BEGIN: PyBryt Python 3.13 compatibility shim (harmless on older Pythons) ---
def _apply_pybryt_py313_shim():
    """
    Make PyBryt's MemoryFootprint / MemoryFootprintIterator safely iterable on Python 3.13
    and harden value matching iteration. No effect on <3.13.
    """
    if sys.version_info < (3, 13):
        return

    try:
        from pybryt.memory import MemoryFootprint, MemoryFootprintIterator  # type: ignore
    except Exception:
        MemoryFootprint = None
        MemoryFootprintIterator = None

    # 1) Ensure BOTH classes return themselves from __iter__
    try:
        if MemoryFootprintIterator is not None:
            # Force (re)define __iter__ to be safe even if it already exists
            def _mfi___iter__(self):
                return self
            MemoryFootprintIterator.__iter__ = _mfi___iter__  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        if MemoryFootprint is not None:
            def _mf___iter__(self):
                # If object supports __next__, returning self makes it a proper iterator.
                return self
            MemoryFootprint.__iter__ = _mf___iter__  # type: ignore[attr-defined]
    except Exception:
        pass

    # 2) Harden Value._get_satisfying_index to iterate robustly
    try:
        from pybryt.annotations.value import Value as _PyBrytValue  # type: ignore
        _orig_get = _PyBrytValue._get_satisfying_index  # keep a handle if you ever want to revert

        def _iter_footprint(fp):
            """
            Robust iterator over a PyBryt footprint for Py 3.13:
            - Try iter(fp)
            - If that fails, try repeatedly next(fp)
            - If that fails, try iter(list(fp)) as last resort
            """
            # Try the normal iterator protocol first
            try:
                it = iter(fp)
                while True:
                    yield next(it)
            except TypeError:
                # Not iterable, maybe it's an iterator (has __next__)
                try:
                    while True:
                        yield next(fp)
                except TypeError:
                    # Last resort: materialize then iterate (might still raise, we swallow below)
                    try:
                        for v in list(fp):
                            yield v
                    except Exception:
                        return
            except StopIteration:
                return

        def _get_satisfying_index(self, footprint):
            expected_value = self.value
            satisfied = []
            try:
                for mfp_val in _iter_footprint(footprint):
                    try:
                        ok = self._check_observed_value(expected_value, mfp_val.value)
                    except Exception:
                        ok = False
                    satisfied.append(ok)
            except Exception:
                # If anything odd happens, fail gracefully (no satisfier)
                pass

            return satisfied.index(True) if any(satisfied) else None

        _PyBrytValue._get_satisfying_index = _get_satisfying_index  # type: ignore[assignment]
    except Exception:
        pass


_apply_pybryt_py313_shim()
# --- END: PyBryt Python 3.13 compatibility shim ---


# def pybryt_reference(lecture, exercise):
#     basename = os.path.join('pybryt-references',
#                             f'exercise-{lecture}_{exercise}')
#     pyfilename = f'{basename}.py'
#     pklfilename = f'{basename}.pkl'

#     if os.path.isfile(pyfilename):
#         pybryt.ReferenceImplementation.compile(pyfilename).dump(pklfilename)
#     elif not os.path.isfile(pklfilename):
#         raise FileNotFoundError('Reference pkl file does not exists.')

#     return pklfilename

def pybryt_reference(lecture, exercise):
    base = os.path.join('pybryt-references', f'exercise-{lecture}_{exercise}')

    main_py  = f'{base}.py'
    main_pkl = f'{base}.pkl'
    refs = []

    if os.path.isfile(main_py):
        pybryt.ReferenceImplementation.compile(main_py).dump(main_pkl)
    elif not os.path.isfile(main_pkl):
        raise FileNotFoundError('Reference pkl file does not exists.')
    refs.append(main_pkl)

    style_py  = f'{base}_style.py'
    style_pkl = f'{base}_style.pkl'
    if os.path.isfile(style_py):
        pybryt.ReferenceImplementation.compile(style_py).dump(style_pkl)
        refs.append(style_pkl)

    return refs if len(refs) > 1 else main_pkl
