"""S09 palette IDs and supported styling, independent of SVG layout."""

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


@pytest.mark.parametrize('group,prefix,names', [
    ('fills','fill-type-', ['clear','water','marsh','rough','urban','unused']),
    ('edges','edge-type-', ['normal','stream','river']),
])
def test_palette_ids_and_lookup(model_page, group, prefix, names):
    actual = model_page.evaluate('''group => Terrain[group].map(x => [
        x.name,x.getUniqueID(),Terrain.idToName(x.getUniqueID()),Terrain.index[x.name] === x])''', group)
    assert actual == [[name, prefix+name, name, True] for name in names]
    assert model_page.evaluate('Terrain.defaultFillName') == 'clear'


@pytest.mark.parametrize('name', ['road','path'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K10: path palette uses edge IDs')
def test_path_palette_id_maps_to_path_style(model_page, name):
    actual = model_page.evaluate('''name => {
        const p = Terrain.paths.find(p => p.name === name), id = p.getUniqueID();
        return [id,Terrain.idToName(id),Terrain.index[name] === p,
                Boolean(Style.terrainPathIndex[Terrain.idToName(id)])];
    }''', name)
    if actual == ['edge-type-'+name, name, True, True]:
        raise KnownDefect('K10: path name resolves but the palette ID has the wrong category')
    assert actual == ['path-type-'+name, name, True, True]


def test_all_supported_styles(model_page):
    actual = model_page.evaluate('''() => ({fills:Style.terrainFillIndex,
        edges:Style.terrainEdgeIndex, paths:Style.terrainPathIndex,
        factions:Style.factionIndex,
        supported: [['fills','terrainFillIndex'],['edges','terrainEdgeIndex'],
                    ['paths','terrainPathIndex']].every(([group,index]) =>
            Terrain[group].every(p => Terrain.idToName(p.getUniqueID()) in Style[index]))})''')
    assert actual == dict(
        fills=dict(clear='white',water='powderblue',marsh='palegreen',rough='wheat',urban='lightgray',unused='gray'),
        edges=dict(normal=dict(color='black',width=0.1),stream=dict(color='blue',width=0.3),river=dict(color='blue',width=0.5)),
        paths=dict(road=dict(color='black',width=0.2),path=dict(color='gray',width=0.2)),
        factions=dict(red=dict(dim='#e0abab',normal='#fcc5c5',bright='#ffd4d4'),
                      blue=dict(dim='#ababe0',normal='#c5c5fc',bright='#d4d4ff')),supported=True)
