from sampleapp.models import LTreeModelTest


def test_ltree():
    parent = LTreeModelTest.objects.create(name='parent')
    child = LTreeModelTest.objects.create(name='child', parent=parent)
    grandchild = LTreeModelTest.objects.create(name='grandchild', parent=child)

    assert list(
        LTreeModelTest.objects.filter(
            ltree_label_path__descendants=parent.ltree_label_path
        ).values_list(
            'name', flat=True,
        )
    ) == [
        parent.name,
        child.name,
        grandchild.name,
    ]

    assert list(
        LTreeModelTest.objects.filter(
            ltree_label_path__nlevel=2,
        ).values_list(
            'name', flat=True,
        )
    ) == [
        child.name,
    ]
