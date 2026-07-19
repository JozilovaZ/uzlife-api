"""Har bir kategoriyaga 20 tadan boy matnli, rasmli demo yangilik yaratadi.

Ishlatish:
    python manage.py seed_rich          # 20 tadan to‘ldiradi
    python manage.py seed_rich --flush  # avval eski maqolalarni o‘chiradi
"""
import io
import random
import textwrap
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from PIL import Image, ImageDraw, ImageFont

from apps.news.models import Article, Category

PER_CATEGORY = 20

# Kategoriya -> (rang, 20 ta sarlavha)
CAT_COLOR = {
    'Siyosat': (37, 99, 235),
    'Iqtisod': (5, 150, 105),
    'Jamiyat': (219, 39, 119),
    'Dunyo': (2, 132, 199),
    'Sport': (234, 88, 12),
    'Texnologiya': (124, 58, 237),
    'Madaniyat': (190, 24, 93),
    'Ta’lim': (202, 138, 4),
}

TITLES = {
    'Siyosat': [
        'Parlament yangi qonun loyihasini birinchi o‘qishda ma’qulladi',
        'Prezident mintaqaviy hamkorlik masalalarini muhokama qildi',
        'Yangi islohotlar dasturi jamoatchilik muhokamasiga qo‘yildi',
        'Deputatlar byudjet taqsimoti bo‘yicha kelishuvga erishdi',
        'Diplomatik uchrashuvda ikki tomonlama savdo kelishildi',
        'Senat yangi vazir nomzodini tasdiqladi',
        'Mahalliy kengashlar saylovi sanasi e’lon qilindi',
        'Davlat dasturi ijrosi bo‘yicha hisobot taqdim etildi',
        'Konstitutsiyaviy islohotlar bo‘yicha muhokamalar davom etmoqda',
        'Hukumat yangi ijtimoiy kafolatlar to‘plamini ma’qulladi',
        'Xalqaro delegatsiya poytaxtga tashrif buyurdi',
        'Yangi shaffoflik va ochiqlik tashabbusi ishga tushirildi',
        'Fuqarolar murojaatlari bo‘yicha yagona tizim yangilandi',
        'Mintaqaviy rivojlanish strategiyasi tasdiqlandi',
        'Davlat xizmatchilari uchun yangi malaka talablari kiritildi',
        'Qonunchilik palatasida navbatdagi yalpi majlis o‘tkazildi',
        'Milliy xavfsizlik kengashi navbatdagi majlisini o‘tkazdi',
        'Ma’muriy islohotlar bo‘yicha yangi yo‘l xaritasi tasdiqlandi',
        'Ikki davlat o‘rtasida strategik sheriklik memorandumi imzolandi',
        'Saylov qonunchiligiga o‘zgartirishlar kiritish taklif etildi',
    ],
    'Iqtisod': [
        'Markaziy bank asosiy stavkani o‘zgarishsiz qoldirdi',
        'Kichik biznes uchun yangi soliq imtiyozlari joriy etildi',
        'Eksport hajmi o‘tgan yilga nisbatan sezilarli oshdi',
        'Investitsiya muhitini yaxshilash bo‘yicha chora-tadbirlar e’lon qilindi',
        'Milliy valyuta kursi barqarorligicha qolmoqda',
        'Inflyatsiya darajasi bashoratlarga mos pasaydi',
        'Yangi erkin iqtisodiy zona tashkil etildi',
        'Bank sektorida raqamli to‘lovlar hajmi rekord darajaga yetdi',
        'Qishloq xo‘jaligi mahsulotlari eksporti kengaymoqda',
        'Xorijiy sarmoyadorlar bilan yirik shartnomalar imzolandi',
        'Ish o‘rinlari yaratish dasturi natijalari e’lon qilindi',
        'Energetika tarmog‘iga sarmoya kiritish oshdi',
        'Yangi sanoat klasteri ishga tushirildi',
        'Aholi daromadlari bo‘yicha statistik hisobot chiqdi',
        'Kredit stavkalari tadbirkorlar uchun qulaylashtirildi',
        'To‘qimachilik sanoati eksport hajmini oshirdi',
        'Yalpi ichki mahsulot o‘sishi ijobiy dinamikani saqlab qolmoqda',
        'Yangi logistika markazi savdo aylanmasini tezlashtiradi',
        'Davlat-xususiy sheriklik loyihalari hajmi kengaydi',
        'Mintaqalarda ishbilarmonlik faolligi indeksi ko‘tarildi',
    ],
    'Jamiyat': [
        'Toshkent metrosida yangi bekat foydalanishga topshirildi',
        'Ta’lim tizimida raqamli xizmatlar kengaytirilmoqda',
        'Jamoat transporti uchun yangi tariflar joriy etiladi',
        'Poytaxtda yashil hududlar maydoni kengaytirilmoqda',
        'Sog‘liqni saqlash tizimida navbatsiz qabul yo‘lga qo‘yildi',
        'Yangi ijtimoiy uy-joy dasturi start oldi',
        'Ko‘p bolali oilalarga qo‘shimcha yordam belgilandi',
        'Shaharda yangi bolalar bog‘chalari ochildi',
        'Ichimlik suvi ta’minoti loyihasi yakunlandi',
        'Ko‘chalarni obodonlashtirish ishlari boshlandi',
        'Aholiga bepul huquqiy maslahat markazlari ochildi',
        'Yoshlar tashabbuslari uchun grant tanlovi e’lon qilindi',
        'Nogironligi bor shaxslar uchun muhit moslashtirildi',
        'Yangi zamonaviy poliklinika qurib bitkazildi',
        'Ekologik toza transport parki kengaytirildi',
        'Mahallalarda raqamli xizmatlar joriy etildi',
        'Shahar chetida yangi park va istirohat bog‘i ochildi',
        'Aholini ish bilan ta’minlash yarmarkasi o‘tkazildi',
        'Ko‘cha yoritish tizimi energiya tejamkor chiroqlarga o‘tkazildi',
        'Volontyorlar harakati yangi ijtimoiy loyihani boshladi',
    ],
    'Dunyo': [
        'Mintaqada iqtisodiy hamkorlik bo‘yicha yangi bitim imzolandi',
        'Xalqaro sammitda iqlim masalalari muhokama qilindi',
        'Yetakchi davlatlar energetika kelishuviga erishdi',
        'Jahon bozorida neft narxi o‘zgardi',
        'Xalqaro tashkilot yangi gumanitar dasturni e’lon qildi',
        'Yirik davlatlar savdo kelishuvini yangiladi',
        'Jahon iqtisodiyoti o‘sish sur’atlari qayta baholandi',
        'Xalqaro kosmik missiya muvaffaqiyatli yakunlandi',
        'Yevropada energetika narxlari bo‘yicha kelishuv bo‘ldi',
        'Osiyo mintaqasida yangi savdo yo‘laklari ochildi',
        'Global texnologiya sammiti ish boshladi',
        'BMT yangi barqaror rivojlanish hisobotini taqdim etdi',
        'Xalqaro valyuta bozorida o‘zgarishlar kuzatilmoqda',
        'Yirik xalqaro forum yakunida deklaratsiya qabul qilindi',
        'Diplomatik muzokaralar yangi bosqichga o‘tdi',
        'Jahon sog‘liqni saqlash tashkiloti yangi tavsiyalar berdi',
        'Xalqaro sport hamjamiyati yangi qoidalarni tasdiqladi',
        'Yetakchi davlatlar sun’iy intellekt bo‘yicha muzokara o‘tkazdi',
        'Mintaqaviy tashkilot navbatdagi sammitini o‘tkazdi',
        'Global oziq-ovqat xavfsizligi masalasi muhokama qilindi',
    ],
    'Sport': [
        'Terma jamoa navbatdagi o‘yinga tayyorgarlik ko‘rmoqda',
        'Futbol chempionatida navbatdagi tur natijalari ma’lum bo‘ldi',
        'Kurashchilarimiz xalqaro turnirda medal qo‘lga kiritdi',
        'Yangi sport majmuasi ochilish marosimi bo‘lib o‘tdi',
        'Olimpiya saralashida yurtdoshimiz yo‘llanma oldi',
        'Bokschilarimiz jahon chempionatida g‘alaba qozondi',
        'Yengil atletika bo‘yicha yangi milliy rekord o‘rnatildi',
        'Yoshlar terma jamoasi finalga chiqdi',
        'Tennis turnirida yurtdoshimiz yarim finalga yetdi',
        'Sport gimnastikasi bo‘yicha musobaqa yakunlandi',
        'Futbolchimiz xorijiy klubga transfer bo‘ldi',
        'Og‘ir atletika terma jamoasi medallarni qo‘lga kiritdi',
        'Shaxmat bo‘yicha xalqaro turnir start oldi',
        'Velosport poyga marafoni bo‘lib o‘tdi',
        'Milliy liga mavsumi rasman ochildi',
        'Paralimpiya sportchilari yangi yutuqlarga erishdi',
        'Suzuvchilarimiz kontinental chempionatda kurashadi',
        'Yosh iqtidorlar uchun yangi sport maktabi ochildi',
        'Milliy terma jamoa bosh murabbiyi matbuot anjumani o‘tkazdi',
        'Judochilarimiz Gran-pri bosqichida ishtirok etmoqda',
    ],
    'Texnologiya': [
        'Mahalliy startaplar uchun yangi grant dasturi ishga tushdi',
        'Mobil operatorlar 5G tarmog‘ini kengaytirishni boshladi',
        'Sun’iy intellekt bo‘yicha milliy strategiya taqdim etildi',
        'Raqamli hukumat xizmatlari yangi bosqichga o‘tdi',
        'IT-parkda yangi rezidentlar soni oshdi',
        'Elektron tijorat platformalari auditoriyasi kengaydi',
        'Kiberxavfsizlik markazi yangi tizimni ishga tushirdi',
        'Yoshlar uchun bepul dasturlash kurslari ochildi',
        'Yangi ma’lumotlar markazi qurilishi yakunlandi',
        'Fintech kompaniyalari yangi xizmatlarni taqdim etdi',
        'Robototexnika bo‘yicha milliy tanlov o‘tkazildi',
        'IT-eksport hajmi rekord ko‘rsatkichga yetdi',
        'Sun’iy intellekt asosidagi xizmatlar joriy etilmoqda',
        'Bulutli texnologiyalarga o‘tish sur’atlari oshdi',
        'Ta’limda raqamli platformalar keng qo‘llanmoqda',
        'Yangi mahalliy smartfon ishlab chiqarish yo‘lga qo‘yildi',
        'Ochiq kodli dasturlar hamjamiyati kengaymoqda',
        'Elektromobillar uchun quvvatlash tarmog‘i kengaytirilmoqda',
        'Raqamli identifikatsiya tizimi yangi imkoniyatlar bilan boyidi',
        'Milliy superkompyuter loyihasi taqdim etildi',
    ],
    'Madaniyat': [
        'Xalqaro kinofestival g‘oliblari e’lon qilindi',
        'Milliy teatrda yangi mavsum ochildi',
        'Zamonaviy san’at ko‘rgazmasi tashrifchilarni jalb qilmoqda',
        'Adabiyot mukofoti sovrindorlari taqdirlandi',
        'Muzey fondi noyob eksponatlar bilan boyidi',
        'Milliy kino yangi filmi keng ekranlarga chiqdi',
        'Xalq hunarmandchiligi festivali bo‘lib o‘tdi',
        'Yosh rassomlar ko‘rgazmasi ochildi',
        'Klassik musiqa konserti tomoshabinlarni jalb qildi',
        'Kitob ko‘rgazmasi minglab tashrifchilarni yig‘di',
        'Milliy meros obidalari ta’mirlandi',
        'Xalqaro teatr festivali start oldi',
        'Zamonaviy raqs guruhi yangi dasturini taqdim etdi',
        'Madaniy meros ro‘yxatiga yangi ob’ektlar kiritildi',
        'Poytaxtda yangi zamonaviy kutubxona ochildi',
        'Milliy libos ko‘rgazmasi katta qiziqish uyg‘otdi',
        'Xalqaro musiqa festivali ishtirokchilarni to‘pladi',
        'Yosh yozuvchilar uchun ijodiy seminar o‘tkazildi',
        'Milliy filarmoniya yangi konsert dasturini taqdim etdi',
        'Zamonaviy me’morchilik ko‘rgazmasi ochildi',
    ],
    'Ta’lim': [
        'Maktablarda yangi o‘quv yili tayyorgarligi yakunlandi',
        'Universitetlarga qabul kvotalari e’lon qilindi',
        'Xalqaro grant dasturi uchun ariza qabuli boshlandi',
        'Yangi zamonaviy maktab binosi foydalanishga topshirildi',
        'O‘qituvchilar malakasini oshirish kurslari yangilandi',
        'Milliy sertifikat imtihonlari jadvali ma’lum bo‘ldi',
        'Xorijiy universitetlar filiallari soni ko‘paydi',
        'Maktab o‘quvchilari xalqaro olimpiadada g‘olib chiqdi',
        'Kasb-hunar ta’limi yo‘nalishlari kengaytirildi',
        'Elektron kunlik va baholash tizimi takomillashtirildi',
        'Talabalar uchun stipendiya miqdori oshirildi',
        'Masofaviy ta’lim platformalari yangi kurslar bilan boyidi',
        'Boshlang‘ich sinflarda yangi darsliklar joriy etildi',
        'Oliy ta’limda kredit-modul tizimi kengaytirildi',
        'Iqtidorli yoshlarni qo‘llab-quvvatlash jamg‘armasi tuzildi',
        'STEAM ta’limi bo‘yicha yangi laboratoriyalar ochildi',
        'Maktabgacha ta’lim qamrovi sezilarli oshdi',
        'Xalqaro reyting uchun universitetlar hamkorligi kuchaydi',
        'Pedagoglar uchun raqamli kompetensiya kurslari ochildi',
        'O‘quvchilar uchun bepul repetitorlik platformasi ishga tushdi',
    ],
}

# Boy matn uchun paragraf shablonlari
PARAGRAPHS = [
    'Mutaxassislarning ta’kidlashicha, ushbu qadam sohadagi uzoq muddatli '
    'islohotlarning mantiqiy davomi bo‘lib, kelgusi bir necha yil davomida '
    'sezilarli natijalar berishi kutilmoqda. Tegishli idoralar tomonidan '
    'zarur hujjatlar allaqachon tayyorlangan va bosqichma-bosqich amalga '
    'oshiriladi.',

    'Voqealar rivojini kuzatib borayotgan ekspertlar bu boradagi '
    'yangiliklarni ijobiy baholamoqda. Ularning fikricha, hozirgi shart-'
    'sharoitlar keyingi rejalarni muvaffaqiyatli ro‘yobga chiqarish uchun '
    'yetarli imkoniyat yaratmoqda va aholi manfaatlari birinchi o‘ringa '
    'qo‘yilmoqda.',

    'Rasmiy manbalarning ma’lumot berishicha, jarayon shaffof tarzda '
    'tashkil etilgan bo‘lib, har bir bosqich ochiq muhokama qilinadi. '
    'Fuqarolarning takliflari va e’tirozlari maxsus platforma orqali '
    'qabul qilinib, yakuniy qarorda inobatga olinadi.',

    'Statistik ko‘rsatkichlar so‘nggi davrda barqaror o‘sish kuzatilayotganini '
    'tasdiqlaydi. Tahlilchilar bu tendensiya davom etsa, yaqin kelajakda '
    'yanada yuqori natijalarga erishish mumkinligini bashorat qilmoqda.',

    'Loyihaning tashabbuskorlari mahalliy va xalqaro hamkorlar bilan yaqindan '
    'ishlashini ma’lum qildi. Bu esa ilg‘or tajribani o‘zlashtirish, zamonaviy '
    'texnologiyalarni joriy etish va sifatni oshirish imkonini beradi.',

    'Yakunda tashkilotchilar barcha manfaatdor tomonlarga minnatdorchilik '
    'bildirdi va navbatdagi bosqichlar haqida qo‘shimcha ma’lumotlar yaqin '
    'kunlarda e’lon qilinishini aytdi. Jamoatchilik voqealardan doimiy '
    'xabardor qilib boriladi.',
]

SUMMARY_TPL = (
    '{title} — bu boradagi so‘nggi ma’lumotlar, mutaxassis izohlari va '
    'batafsil tafsilotlar bilan tanishing.'
)


def _font(size):
    for path in (
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_cover(title, cat_name, color):
    """Kategoriya rangida gradientli, sarlavhali muqova rasm yaratadi."""
    w, h = 1200, 630
    img = Image.new('RGB', (w, h), color)
    top = color
    bottom = tuple(max(0, int(c * 0.55)) for c in color)
    for y in range(h):
        t = y / h
        row = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=row)

    d = ImageDraw.Draw(img)
    # Kategoriya yorlig‘i
    d.rectangle([60, 60, 60 + 24 + len(cat_name) * 22, 120], fill=(255, 255, 255))
    d.text((84, 74), cat_name.upper(), font=_font(34), fill=color)

    # Sarlavha (o‘ralgan)
    title_font = _font(58)
    lines = textwrap.wrap(title, width=26)[:5]
    y = 240
    for line in lines:
        d.text((60, y), line, font=title_font, fill=(255, 255, 255))
        y += 74

    d.text((60, h - 70), 'UzLife • yangilik_uz', font=_font(30), fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'Har bir kategoriyaga 20 tadan boy matnli, rasmli yangilik yaratadi.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Avval barcha maqolalarni o‘chiradi.')

    def handle(self, *args, **opts):
        if opts['flush']:
            n = Article.objects.count()
            Article.objects.all().delete()
            self.stdout.write(f'{n} ta eski maqola o‘chirildi.')

        now = timezone.now()
        created = 0
        for order, (cat_name, titles) in enumerate(TITLES.items(), start=1):
            color = CAT_COLOR.get(cat_name, (37, 99, 235))
            category, _ = Category.objects.get_or_create(
                name=cat_name, defaults={'order': order},
            )
            for i, title in enumerate(titles[:PER_CATEGORY]):
                if Article.objects.filter(title=title).exists():
                    continue

                # Boy matn: 4-6 paragraf
                body_parts = [title + '.']
                body_parts += random.sample(PARAGRAPHS, k=random.randint(4, 6))
                body = '\n\n'.join(body_parts)

                article = Article(
                    title=title,
                    summary=SUMMARY_TPL.format(title=title),
                    body=body,
                    category=category,
                    status=Article.Status.PUBLISHED,
                    is_featured=(order == 1 and i == 0),
                    views_count=random.randint(200, 5000),
                    published_at=now - timedelta(hours=order * 3 + i),
                )
                article.save()
                fname = f'{category.slug or "news"}-{i + 1}.jpg'
                article.cover_image.save(
                    fname, make_cover(title, cat_name, color), save=True,
                )
                created += 1
                self.stdout.write(f'  + {cat_name}: {title[:40]}…')

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {Category.objects.count()} kategoriya, '
            f'{created} ta yangi rasmli maqola. '
            f'Jami: {Article.objects.count()} maqola.'
        ))
