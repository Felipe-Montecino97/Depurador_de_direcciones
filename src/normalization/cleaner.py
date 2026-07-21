import csv
from pathlib import Path
import re
import unicodedata


ABBREVIATIONS = {
    "av": "avenida",
    "av.": "avenida",
    "avda": "avenida",
    "aven": "avenida",
    "cal": "calle",
    "cll": "calle",
    "pj": "pasaje",
    "pje": "pasaje",
    "psje": "pasaje",
    "pobl": "poblacion",
    "pob": "poblacion",
    "depto": "departamento",
    "dpto": "departamento",
    "dep": "departamento",
    "of": "oficina",
    "ofi": "oficina",
    "nro": "numero",
    "num": "numero",
    "n": "numero",
    "n°": "numero",
    "#": "numero",
    "stgo": "santiago",
}

MEANINGFUL_SHORT_TOKENS = {"n", "b", "a", "km"}

MASTER_CATALOG_PATH = Path("Maestro/output/maestro_territorial_chile.csv")
ALIAS_CATALOG_PATH = Path("Maestro/output/alias_territorial_chile.csv")

KNOWN_TEXT_REPLACEMENTS = {
    "torreconcepcion": "torre concepcion",
    "manantialesvaldivia": "manantiales valdivia",
    "mistrallas": "mistral las",
    "animaslas": "animas las",
    "dechilemaipu": "de chile maipu",
    "sabellaantofagasta": "sabella antofagasta",
    "estrellapudahuel": "estrella pudahuel",
    "condoromalos": "condoroma los",
    "nalcahuesan": "nalcahue san",
    "diegoportales": "diego portales",
    "penonsotero": "penon sotero",
    "costaneratalagante": "costanera talagante",
    "centralquilicura": "central quilicura",
    "quellonquellon": "quellon quellon",
    "salinastalcahuano": "salinas talcahuano",
    "puntillapirque": "puntilla pirque",
    "cantohualpen": "canto hualpen",
    "franckepuyehue": "francke puyehue",
    "catalunacurico": "cataluna curico",
    "tierraamarilla": "tierra amarilla",
    "garridocurico": "garrido curico",
    "candilescolina": "candiles colina",
    "alpesrancagua": "alpes rancagua",
    "capillarancagua": "capilla rancagua",
    "americashualpen": "americas hualpen",
    "antunesquillota": "antunes quillota",
    "cobretocopilla": "cobre tocopilla",
    "cantarosquilicura": "cantaros quilicura",
    "melefquenpanguipulli": "melefquen panguipulli",
    "pomairemelipilla": "pomaire melipilla",
    "josemelipilla": "jose melipilla",
    "mexicocerrillos": "mexico cerrillos",
    "maisanpitrufquen": "maisan pitrufquen",
    "grandesalamanca": "grande salamanca",
    "alamoscopiapo": "alamos copiapo",
    "amanecertemuco": "amanecer temuco",
    "caspanacalama": "caspana calama",
    "mirafloresmiraflores": "miraflores",
    "morenoantofagasta": "moreno antofagasta",
    "hondoquilpue": "hondo quilpue",
    "gracielacoronel": "graciela coronel",
    "ricomariquina": "rico mariquina",
    "portalovalle": "portal ovalle",
    "cooprevalquillota": "coopreval quillota",
    "curaumaplacilla": "curauma placilla",
    "marinaquilicura": "marina quilicura",
    "mistralantofagasta": "mistral antofagasta",
    "juancoquimbo": "juan coquimbo",
    "romeropenaflor": "romero penaflor",
    "damianrancagua": "damian rancagua",
    "cisnesvaldivia": "cisnes valdivia",
    "centroconcepcion": "centro concepcion",
    "centrocalama": "centro calama",
    "martinputaendo": "martin putaendo",
    "carvallograneros": "carvallo graneros",
    "raucorauco": "rauco",
    "triangulohualpen": "triangulo hualpen",
    "travesiaiquique": "travesia iquique",
    "tejavaldivia": "teja valdivia",
    "eugeniaquilicura": "eugenia quilicura",
    "nortecoquimbo": "norte coquimbo",
    "magisteriochillan": "magisterio chillan",
    "departamentorancagua": "departamento rancagua",
    "calamacalama": "calama",
    "combarbalacombarbala": "combarbala",
    "maulesaavedra": "maule saavedra",
    "baronbaron": "baron",
    "quilastemuco": "quilas temuco",
    "talhuencanela": "talhuen canela",
    "vilcunvilcun": "vilcun",
    "valdiviavaldivia": "valdivia",
    "coronelcoronel": "coronel",
    "villarricavillarrica": "villarrica",
    "chiguayantechiguayante": "chiguayante",
    "araucoarauco": "arauco",
    "penaflorpenaflor": "penaflor",
    "puchuncavipuchuncavi": "puchuncavi",
    "machalimachali": "machali",
    "lonquimaylonquimay": "lonquimay",
    "mallocopenaflor": "malloco penaflor",
    "porvenirchiguayante": "porvenir chiguayante",
    "llanocoquimbo": "llano coquimbo",
    "rauquencurico": "rauquen curico",
    "grandevalle": "grande valle",
    "orienterancagua": "oriente rancagua",
    "anamaipu": "ana maipu",
    "arenasconcepcion": "arenas concepcion",
    "quinelcabrero": "quinel cabrero",
    "santaagua": "santa agua",
    "torreblancavallenar": "torreblanca vallenar",
    "grandecurico": "grande curico",
    "allendecollipulli": "allende collipulli",
    "campinaquilicura": "campina quilicura",
    "olivarantofagasta": "olivar antofagasta",
    "britolimache": "brito limache",
    "copihuesllay": "copihues llay",
    "arrayanesosorno": "arrayanes osorno",
    "cortijoel": "cortijo el",
    "amapolaschillan": "amapolas chillan",
    "carmentemuco": "carmen temuco",
    "esperanzacopiapo": "esperanza copiapo",
    "andaliencurico": "andalien curico",
    "molinonancagua": "molino rancagua",
    "ohigginscalama": "ohiggins calama",
    "arismendicurico": "arismendi curico",
    "sabinatalcahuano": "sabina talcahuano",
    "porvenirmelipilla": "porvenir melipilla",
    "alcaldespanguipulli": "alcaldes panguipulli",
    "coraleschiguayante": "corales chiguayante",
    "casonaquilicura": "casona quilicura",
    "grandonantofagasta": "grandon antofagasta",
    "paipotecopiapo": "paipote copiapo",
    "lourdesrancagua": "lourdes rancagua",
    "granjamulchen": "granja mulchen",
    "rucatremocurico": "rucatremo curico",
    "bosquevaldivia": "bosque valdivia",
    "irarrazabalantofagasta": "irarrazabal antofagasta",
    "saladotalagante": "salado talagante",
    "rosariocopiapo": "rosario copiapo",
    "ineschiguayante": "ines chiguayante",
    "antumalentemuco": "antumalal temuco",
    "olivosparral": "olivos parral",
    "centenarioosorno": "centenario osorno",
    "pencopenco": "penco",
    "josechimbarongo": "jose chimbarongo",
    "marcosromeral": "marcos romeral",
    "sindempartcoquimbo": "sindempart coquimbo",
    "febrrorancagua": "febrero rancagua",
    "allendecoronel": "allende coronel",
    "aylwinhualpen": "aylwin hualpen",
    "amaneceryumbel": "amanecer yumbel",
    "ayquinacalama": "ayquina calama",
    "nerudalinares": "neruda linares",
    "cordillerachillan": "cordillera chillan",
    "orientechillan": "oriente chillan",
    "higuerastalcahuano": "higueras talcahuano",
    "llanmos": "llanos",
    "camaricoovalle": "camarico ovalle",
    "arocahualpen": "aroca hualpen",
    "sofiavaldivia": "sofia valdivia",
    "rosapenaflor": "rosa penaflor",
    "millauquenquilicura": "millauquen quilicura",
    "curqueandacollo": "curque andacollo",
    "salarescopiapo": "salares copiapo",
    "amanecerquillota": "amanecer quillota",
    "alemaniacalama": "alemania calama",
    "atenaspenalolen": "atenas penalolen",
    "lobostalcahuano": "lobos talcahuano",
    "vicentetalcahuano": "vicente talcahuano",
    "higginscalama": "higgins calama",
    "ibietarancagua": "ibieta rancagua",
    "companiavicuna": "compania vicuna",
    "corvallisantofagasta": "corvallis antofagasta",
    "condorestalcahuano": "condores talcahuano",
    "cristobalchillan": "cristobal chillan",
    "mackennarancagua": "mackenna rancagua",
    "peldehuecolina": "peldehue colina",
    "vegamelipilla": "vega melipilla",
    "castanosgraneros": "castanos graneros",
    "bosquespenaflor": "bosques penaflor",
    "nortequintero": "norte quintero",
    "verdecuranilahue": "verde curanilahue",
    "paunguemelipilla": "paungue melipilla",
    "halconesovalle": "halcones ovalle",
    "pinosquilpue": "pinos quilpue",
    "schneiderrancagua": "schneider rancagua",
    "palomarcopiapo": "palomar copiapo",
    "urmenetarancagua": "urmeneta rancagua",
    "enamiquintero": "enami quintero",
    "labranzatemuco": "labranza temuco",
    "hermosacalama": "hermosa calama",
    "carmenlongavi": "carmen longavi",
    "marcoletaquilicura": "marcoleta quilicura",
    "porvenirquilpue": "porvenir quilpue",
    "carrizoantofagasta": "carrizo antofagasta",
    "luisquilicura": "luis quilicura",
    "ichiguayante": "i chiguayante",
    "pieddra": "piedra",
    "mehuinmehuin": "mehuin",
    "nortechiguayante": "norte chiguayante",
    "exoticacalama": "exotica calama",
    "militartemuco": "militar temuco",
    "alemaniaantofagasta": "alemania antofagasta",
    "viazulpudahuel": "via azul pudahuel",
    "campinoquilicura": "campino quilicura",
    "tranquerasquilicura": "tranqueras quilicura",
    "parcelatalagante": "parcela talagante",
    "costanerahualpen": "costanera hualpen",
    "lautaroantofagasta": "lautaro antofagasta",
    "canquencolina": "canquen colina",
    "condominioiquique": "condominio iquique",
    "matiziquique": "matiz iquique",
    "curtiduriapencahue": "curtiduria pencahue",
    "herraduracoquimbo": "herradura coquimbo",
    "snpichidegua": "sn pichidegua",
    "fernandopencahue": "fernando pencahue",
    "hornopirenhualaihue": "hornopiren hualaihue",
    "auroraovalle": "aurora ovalle",
    "tongoytongoy": "tongoy",
    "ruralcalbuco": "rural calbuco",
    "tomaschiguayante": "tomas chiguayante",
    "husaresrancagua": "husares rancagua",
    "girasolesrancagua": "girasoles rancagua",
    "achiguayante": "a chiguayante",
    "ariztiaovalle": "ariztia ovalle",
    "lauquenmulchen": "lauquen mulchen",
    "queulesconcepcion": "queules concepcion",
    "torosmelipilla": "toros melipilla",
    "floridaantofagasta": "florida antofagasta",
    "libertadtalcahuano": "libertad talcahuano",
    "mariamachali": "maria machali",
    "volcanescopiapo": "volcanes copiapo",
    "monacotalagante": "monaco talagante",
    "norteconcepcion": "norte concepcion",
    "galilearancagua": "galilea rancagua",
    "chacabucocolina": "chacabuco colina",
    "rioconcepcion": "rio concepcion",
    "hospicioiquique": "hospicio iquique",
    "solarhualpen": "solar hualpen",
    "aguilacabrero": "aguila cabrero",
    "amanecerrequinoa": "amanecer requinoa",
    "intconcepcion": "int concepcion",
    "melipillamelipilla": "melipilla",
    "illapelillapel": "illapel",
    "concepcionconcepcion": "concepcion",
    "norteantofagasta": "norte antofagasta",
    "carrosromeral": "carros romeral",
    "almendroscalera": "almendros calera",
    "joaquinrancagua": "joaquin rancagua",
    "ascotacalama": "ascota calama",
    "altacoquimbo": "alta coquimbo",
    "alerceshuechuraba": "alerces huechuraba",
    "luisaquilicura": "luisa quilicura",
    "puchacayconcepcion": "puchacay concepcion",
    "taguacochamo": "tagua cochamo",
    "maitenmachali": "maiten machali",
    "blancaantofagasta": "blanca antofagasta",
    "villucochiguayante": "villuco chiguayante",
    "zanartuconcepcion": "zanartu concepcion",
    "cousinopenalolen": "cousino penalolen",
    "obrerososorno": "obreros osorno",
    "manzanalrancagua": "manzanal rancagua",
    "triunfocoquimbo": "triunfo coquimbo",
    "nevadolinares": "nevado linares",
    "puyehueantofagasta": "puyehue antofagasta",
    "surchiguayante": "sur chiguayante",
    "bantofagasta": "b antofagasta",
    "rosaleschillan": "rosales chillan",
    "amanecercoronel": "amanecer coronel",
    "merinovaldivia": "merino valdivia",
    "valenzuelarancagua": "valenzuela rancagua",
    "infantaantofagasta": "infanta antofagasta",
    "castanosnacimiento": "castanos nacimiento",
    "arribacasablanca": "arriba casablanca",
    "centrovallenar": "centro vallenar",
    "viaantofagasta": "via antofagasta",
    "clasicososorno": "clasicos osorno",
    "trebolarcalera": "trebolar calera",
    "iquiqueantofagasta": "iquique antofagasta",
    "apumanquecurico": "apumanque curico",
    "painerancagua": "paine rancagua",
    "riosnacimiento": "rios nacimiento",
    "castillomachali": "castillo machali",
    "ensenadatalcahuano": "ensenada talcahuano",
    "lomasnegrete": "lomas negrete",
    "lopezantofagasta": "lopez antofagasta",
    "coviefiantofagasta": "coviefi antofagasta",
    "valenciaquilpue": "valencia quilpue",
    "surtalcahuano": "sur talcahuano",
    "cerilloslongavi": "cerillos longavi",
    "primaveraconcon": "primavera concon",
    "araucanialautaro": "araucania lautaro",
    "ohigginscolbun": "ohiggins colbun",
    "azulantofagasta": "azul antofagasta",
    "almeydacopiapo": "almeyda copiapo",
    "victoriaquintero": "victoria quintero",
    "araucariasarauco": "araucarias arauco",
    "universopudahuel": "universo pudahuel",
    "vichuquenvichuquen": "vichuquen",
    "torresovalle": "torres ovalle",
    "carloscoquimbo": "carlos coquimbo",
    "gaviotasconcon": "gaviotas concon",
    "huachocopihuevaldivia": "huachocopihue valdivia",
    "lorcaquillota": "lorca quillota",
    "esperanzapencahue": "esperanza pencahue",
    "potrerocurico": "potrero curico",
    "torinapichidegua": "torina pichidegua",
    "mineralescopiapo": "minerales copiapo",
    "blancascoquimbo": "blancas coquimbo",
    "tiruatirua": "tirua",
    "paraisocalera": "paraiso calera",
    "toribiopenaflor": "toribio penaflor",
    "chincolcopetorca": "chincolco petorca",
    "esperanzallanquihue": "esperanza llanquihue",
    "contuyqueilen": "contuy queilen",
    "dptorancagua": "dpto rancagua",
    "loncotorollanquihue": "loncotoro llanquihue",
    "abrarequinoa": "abra requinoa",
    "jardinesrinconada": "jardines rinconada",
    "poligononogales": "poligono nogales",
    "principalpirque": "principal pirque",
    "lastarriasvaldivia": "lastarrias valdivia",
    "melosillacasablanca": "melosilla casablanca",
    "ameliaretiro": "amelia retiro",
    "catolicosquillota": "catolicos quillota",
    "mercedesquilleco": "mercedes quilleco",
    "pichideguapichidegua": "pichidegua",
    "chocotapuchuncavi": "chocota puchuncavi",
    "morrotalcahuano": "morro talcahuano",
    "pedrorancagua": "pedro rancagua",
    "maristasquillota": "maristas quillota",
    "tunicherancagua": "tuniche rancagua",
    "parquearauco": "parque arauco",
    "benavidesquillota": "benavides quillota",
    "antumapuquillota": "antumapu quillota",
    "romeralhijuelas": "romeral hijuelas",
    "aserrinvillarrica": "aserrin villarrica",
    "victoriavilcun": "victoria vilcun",
    "vertientescatemu": "vertientes catemu",
    "iribarnenancagua": "iribarren rancagua",
    "jardinespichilemu": "jardines pichilemu",
    "santosvillarrica": "santos villarrica",
    "meyncollipulli": "meyn collipulli",
    "provincialrancagua": "provincial rancagua",
    "porvenirrequinoa": "porvenir requinoa",
    "centinelaiquique": "centinela iquique",
    "rayvillarrica": "ray villarrica",
    "obligadocoronel": "obligado coronel",
    "victoriaputaendo": "victoria putaendo",
    "reinarancagua": "reina rancagua",
    "corvivallenar": "corvi vallenar",
    "garzoquillota": "garzo quillota",
    "capricorniograneros": "capricornio graneros",
    "perezchillan": "perez chillan",
    "forestalforestal": "forestal",
    "vergaraconcon": "vergara concon",
    "magallanescoltauco": "magallanes coltauco",
    "hipicovictoria": "hipico victoria",
    "ohigginscoronel": "ohiggins coronel",
    "figueroaquillota": "figueroa quillota",
    "caleracalera": "calera",
    "huachicooptalcahuano": "huachicoop talcahuano",
    "melinkaguaitecas": "melinka guaitecas",
    "pedromostazal": "pedro mostazal",
    "colontalcahuano": "colon talcahuano",
    "jardinrequinoa": "jardin requinoa",
    "bradenrancagua": "braden rancagua",
    "regidoreslautaro": "regidores lautaro",
    "radiataarauco": "radiata arauco",
    "bcuranilahue": "b curanilahue",
    "bchiguayante": "b chiguayante",
    "lirquenlirquen": "lirquen",
    "beatrizchillan": "beatriz chillan",
    "hurtadotocopilla": "hurtado tocopilla",
    "torrescoquimbo": "torres coquimbo",
    "gabrielarinconada": "gabriela rinconada",
    "molinolinares": "molino linares",
    "soltalcahuano": "sol talcahuano",
    "retirocoronel": "retiro coronel",
    "mariapenaflor": "maria penaflor",
    "espanahualpen": "espana hualpen",
    "ventanasvallenar": "ventanas vallenar",
    "rodriguezcopiapo": "rodriguez copiapo",
    "guaiquillocurico": "guaiquillo curico",
    "casutoandacollo": "casuto andacollo",
    "sagrequillota": "sagre quillota",
    "schneidercalama": "schneider calama",
    "torunosgraneros": "torunos graneros",
    "baquedanovallenar": "baquedano vallenar",
    "luciacasablanca": "lucia casablanca",
    "penonesovalle": "penones ovalle",
    "lasquilasosorno": "las quilas osorno",
    "andaluciatalcahuano": "andalucia talcahuano",
    "realquilicura": "real quilicura",
    "andeschillan": "andes chillan",
    "monasteriograneros": "monasterio graneros",
    "vallevallenar": "valle vallenar",
    "montemarconcon": "montemar concon",
    "reconquistarancagua": "reconquista rancagua",
    "jovenrancagua": "joven rancagua",
    "artificiocalera": "artificio calera",
    "favorecedoracalama": "favorecedora calama",
    "filomenachillan": "filomena chillan",
    "rinconadacopiapo": "rinconada copiapo",
    "pucuravillarrica": "pucura villarrica",
    "chimbaovalle": "chimba ovalle",
    "urzuarancagua": "urzua rancagua",
    "invernadamostazal": "invernada mostazal",
    "villalonovalle": "villalon ovalle",
    "cachapoalcachapoal": "cachapoal",
    "negracopiapo": "negra copiapo",
    "vallepenalolen": "valle penalolen",
    "roblesretiro": "robles retiro",
    "miradorovalle": "mirador ovalle",
    "talcatalca": "talca",
    "cantofagasta": "c antofagasta",
    "suizarancagua": "suiza rancagua",
    "unidohualpen": "unido hualpen",
    "arayanesarauco": "arayanes arauco",
    "italiaquillota": "italia quillota",
    "catedralcopiapo": "catedral copiapo",
    "picarquinmostazal": "picarquin mostazal",
    "cordillerarancagua": "cordillera rancagua",
    "conavicooprancagua": "conavicoop rancagua",
    "panimavidacolbun": "panimavida colbun",
    "incaquillota": "inca quillota",
    "rodriguezpenaflor": "rodriguez penaflor",
    "hualpinhualpin": "hualpin",
    "corvillanquihue": "corvi llanquihue",
    "canchaspudahuel": "canchas pudahuel",
    "nevadochillan": "nevado chillan",
    "aconcaguacalera": "aconcagua calera",
    "riachueloriachuelo": "riachuelo",
    "olimpicaquilpue": "olimpica quilpue",
    "chanaralcalera": "chanaral calera",
    "ilocalicanten": "iloca licanten",
    "hermidapenalolen": "hermida penalolen",
    "araucocopiapo": "arauco copiapo",
    "codpacamarones": "codpa camarones",
    "molinosovalle": "molinos ovalle",
    "culipranmelipilla": "culipran melipilla",
    "arboledaquilicura": "arboleda quilicura",
    "condelltalcahuano": "condell talcahuano",
    "pilaymostazal": "pilay mostazal",
    "conovicoopcurico": "conavicoop curico",
    "hortensiastalagante": "hortensias talagante",
    "lunaquilicura": "luna quilicura",
    "altomelipilla": "alto melipilla",
    "comaicocolina": "comaico colina",
    "galvarinopenalolen": "galvarino penalolen",
    "franckeosorno": "francke osorno",
    "sotaquiovalle": "sotaqui ovalle",
    "varasgraneros": "varas graneros",
    "lanalhuetalcahuano": "lanalhue talcahuano",
    "veneciacollipulli": "venecia collipulli",
    "chicureochicureo": "chicureo",
    "pereirarancagua": "pereira rancagua",
    "loncovacavillarrica": "loncovaca villarrica",
    "bprovidencia": "b providencia",
    "contaocontao": "contao",
    "aantofagasta": "a antofagasta",
    "canteracoquimbo": "cantera coquimbo",
    "franciscorancagua": "francisco rancagua",
    "aldeacauquenes": "aldea cauquenes",
    "alamedarancagua": "alameda rancagua",
    "velascorancagua": "velasco rancagua",
    "zavalavaldivia": "zavala valdivia",
    "alercealerce": "alerce",
    "bindependencia": "b independencia",
    "hualpenhualpen": "hualpen",
    "centralhualpen": "central hualpen",
    "santofagasta": "san to antofagasta",
    "gorbeagorbea": "gorbea",
    "retiroquilpue": "retiro quilpue",
    "quilicuraquilicura": "quilicura",
    "negretenegrete": "negrete",
    "huepiltucapel": "huepil tucapel",
    "putaendoputaendo": "putaendo",
    "faropenalolen": "faro penalolen",
    "acerohualpen": "acero hualpen",
}


def _load_catalog_suffixes() -> list[str]:
    suffixes: set[str] = set()
    if not MASTER_CATALOG_PATH.exists():
        return []

    with MASTER_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            comuna = str(row.get("nombre_comuna", "")).strip().lower()
            comuna = unicodedata.normalize("NFD", comuna)
            comuna = "".join(char for char in comuna if unicodedata.category(char) != "Mn")
            if not comuna:
                continue
            compact = comuna.replace(" ", "")
            if len(compact) >= 5:
                suffixes.add(compact)

    if ALIAS_CATALOG_PATH.exists():
        with ALIAS_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if str(row.get("tipo", "")).strip().lower() != "comuna":
                    continue
                alias = str(row.get("alias", "")).strip().lower()
                alias = unicodedata.normalize("NFD", alias)
                alias = "".join(char for char in alias if unicodedata.category(char) != "Mn")
                compact = alias.replace(" ", "")
                if len(compact) >= 5:
                    suffixes.add(compact)

    return sorted(suffixes, key=len, reverse=True)


CATALOG_SUFFIXES = _load_catalog_suffixes()


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _apply_known_replacements(text: str) -> str:
    updated = text
    for source, target in KNOWN_TEXT_REPLACEMENTS.items():
        updated = updated.replace(source, target)
    return updated


def _collapse_repeated_phrases(text: str) -> str:
    current = text
    # Colapsa duplicaciones consecutivas exactas de 1 a 3 palabras.
    for size in (3, 2, 1):
        words = current.split()
        if len(words) < size * 2:
            continue

        collapsed: list[str] = []
        index = 0
        while index < len(words):
            phrase_a = words[index : index + size]
            phrase_b = words[index + size : index + (size * 2)]
            if len(phrase_a) == size and phrase_a == phrase_b:
                collapsed.extend(phrase_a)
                index += size * 2
                continue
            collapsed.append(words[index])
            index += 1

        current = " ".join(collapsed)

    current = current.replace("los andeslos andes", "los andes")
    current = current.replace("las animaslas animas", "las animas")
    current = current.replace("el quisco el quisco", "el quisco")
    current = current.replace("quellon quellon", "quellon")
    current = current.replace("tierra amarilla tierra amarilla", "tierra amarilla")
    current = current.replace("longavi longavi", "longavi")
    return current


def _split_catalog_suffix_tokens(text: str) -> str:
    tokens = text.split()
    if not tokens or not CATALOG_SUFFIXES:
        return text

    normalized_tokens: list[str] = []
    for token in tokens:
        updated = token
        if token.isalpha() and len(token) >= 10:
            # Separa tokens que terminan en una comuna conocida: galilearancagua -> galilea rancagua.
            for suffix in CATALOG_SUFFIXES:
                if token == suffix or not token.endswith(suffix):
                    continue
                prefix = token[: -len(suffix)]
                if len(prefix) < 2:
                    continue
                updated = f"{prefix} {suffix}"
                break

        normalized_tokens.extend(updated.split())

    return " ".join(normalized_tokens)


def _split_exact_repeated_tokens(text: str) -> str:
    tokens = text.split()
    if not tokens:
        return text

    expanded: list[str] = []
    for token in tokens:
        if token.isalpha() and len(token) >= 6 and len(token) % 2 == 0:
            half = len(token) // 2
            left = token[:half]
            right = token[half:]
            if left == right:
                expanded.extend([left, right])
                continue
        expanded.append(token)

    return " ".join(expanded)


def clean_address(address: str) -> str:
    if not isinstance(address, str):
        return ""

    text = address.lower().strip()
    text = remove_accents(text)

    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = text.replace(";", " ")
    text = text.replace(":", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = text.replace("#", " # ")

    text = re.sub(r"[^a-z0-9#\s]", " ", text)
    text = re.sub(r"\b(\d+)\s+v\b$", r"\1", text)
    text = re.sub(r"\bv\b$", " ", text)

    words = text.split()

    normalized_words = []
    for word in words:
        normalized = ABBREVIATIONS.get(word, word)

        # Se conservan tokens cortos que aportan contexto útil.
        if len(normalized) == 1 and not normalized.isdigit() and normalized not in MEANINGFUL_SHORT_TOKENS:
            continue

        normalized_words.append(normalized)

    text = " ".join(normalized_words)
    text = _apply_known_replacements(text)
    text = _split_catalog_suffix_tokens(text)
    text = _split_exact_repeated_tokens(text)
    text = _collapse_repeated_phrases(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
