import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.news.models import Article, Category

# Kategoriya nomi -> shu rubrikaga mos demo sarlavhalar
DEMO = {
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
        'Yangi shafflik va ochiqlik tashabbusi ishga tushirildi',
        'Fuqarolar murojaatlari bo‘yicha yagona tizim yangilandi',
        'Mintaqaviy rivojlanish strategiyasi tasdiqlandi',
        'Davlat xizmatchilari uchun yangi malaka talablari kiritildi',
        'Qonunchilik palatasida navbatdagi yalpi majlis o‘tkazildi',
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
    ],
}

SUMMARY = (
    'Mutaxassislar o‘zgarishlarni ijobiy baholamoqda. Tafsilotlar va rasmiy '
    'izohlar yaqin kunlarda e’lon qilinishi kutilmoqda.'
)


class Command(BaseCommand):
    help = 'Bosh sahifa uchun demo kategoriya va yangiliklar yaratadi.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Avval mavjud demo maqolalarni o‘chiradi.')

    def handle(self, *args, **opts):
        if opts['flush']:
            Article.objects.all().delete()
            self.stdout.write('Eski maqolalar o‘chirildi.')

        now = timezone.now()
        order = 0
        created = 0
        for cat_name, titles in DEMO.items():
            order += 1
            category, _ = Category.objects.get_or_create(
                name=cat_name, defaults={'order': order},
            )
            for i, title in enumerate(titles):
                if Article.objects.filter(title=title).exists():
                    continue
                Article.objects.create(
                    title=title,
                    summary=SUMMARY,
                    body=SUMMARY + '\n\n' + SUMMARY,
                    category=category,
                    status=Article.Status.PUBLISHED,
                    is_featured=(order == 1 and i == 0),
                    views_count=random.randint(200, 3000),
                    published_at=now - timedelta(hours=order * 2 + i),
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {Category.objects.count()} kategoriya, {created} yangi maqola.'
        ))
