"""Demo yangiliklarga boy (ko'p abzasli) matn va ichki rasmlar qo'shadi.

Body maydonini HTML sifatida to'ldiradi (detail.html'da `|safe` bilan chiqadi).
Rasmlar picsum.photos'dan yangilik pk'siga bog'langan seed orqali olinadi —
har bir yangilik uchun izchil, takrorlanmaydigan tasvir.
"""
import random
import textwrap

from django.core.management.base import BaseCommand

from apps.news.models import Article

# Har bir kategoriya uchun kirish (yetakchi) abzasi
INTRO = {
    'Siyosat': 'Mamlakatda olib borilayotgan islohotlar va davlat siyosatidagi '
               'so‘nggi o‘zgarishlar jamoatchilik e’tiborida bo‘lib qolmoqda.',
    'Iqtisod': 'Iqtisodiy ko‘rsatkichlar va bozordagi harakatlar tadbirkorlar '
               'hamda oddiy iste’molchilar uchun bir xilda muhim ahamiyat kasb etadi.',
    'Jamiyat': 'Aholining kundalik hayoti va ijtimoiy sohadagi yangiliklar '
               'shaharliklar tomonidan katta qiziqish bilan kutib olinmoqda.',
    'Dunyo': 'Xalqaro maydondagi voqealar mintaqaviy va global jarayonlarga '
             'bevosita ta’sir ko‘rsatmoqda.',
    'Sport': 'Sport ixlosmandlari uchun navbatdagi yangiliklar va sportchilarimiz '
             'erishayotgan natijalar quvonarli xabarlar qatoridan joy olmoqda.',
    'Texnologiya': 'Raqamli texnologiyalar sohasidagi tez sur’atli o‘zgarishlar '
                   'hayotimizning barcha jabhalariga kirib bormoqda.',
    'Madaniyat': 'Madaniyat va san’at hayotidagi yangiliklar milliy qadriyatlarimizni '
                 'boyitishga xizmat qilmoqda.',
    'Ta’lim': 'Ta’lim tizimidagi yangiliklar o‘quvchilar, talabalar va ota-onalar '
              'uchun bevosita amaliy ahamiyatga ega.',
}
DEFAULT_INTRO = ('Ushbu yo‘nalishdagi so‘nggi yangiliklar keng jamoatchilik '
                 'e’tiborini tortmoqda.')

# Umumiy abzaslar to'plami — har bir maqola uchun tasodifiy tanlab, boy matn hosil qilinadi
BODY_POOL = [
    'Mutaxassislarning ta’kidlashicha, ushbu o‘zgarishlar uzoq muddatli istiqbolda '
    'ijobiy samara berishi kutilmoqda. Tegishli idoralar zarur choralarni bosqichma-bosqich '
    'amalga oshirib bormoqda.',

    'Sohaga oid statistik ma’lumotlar tahlil qilinganda, so‘nggi davrda barqaror o‘sish '
    'tendensiyasi kuzatilayotgani ma’lum bo‘ldi. Bu esa qo‘yilgan maqsadlarga erishishda '
    'muhim omil bo‘lib xizmat qilmoqda.',

    'Jamoatchilik vakillari bildirgan fikrlarga ko‘ra, aynan shu yo‘nalishdagi ishlar '
    'aholining kundalik hayotini sezilarli darajada yengillashtiradi. Fikr-mulohazalar '
    'inobatga olingan holda ish rejalari takomillashtirilmoqda.',

    'Rasmiy manbalarda qayd etilishicha, loyihaning navbatdagi bosqichi yaqin oylarda '
    'ishga tushiriladi. Bunda ilg‘or tajriba va zamonaviy yondashuvlardan keng foydalanish '
    'ko‘zda tutilgan.',

    'Ekspertlar ushbu qadamni to‘g‘ri yo‘nalishda tashlangan izchil harakatlar sifatida '
    'baholamoqda. Ularning fikricha, natijalar yaqin kelajakda yaqqol seziladi.',

    'Shuningdek, mavzu yuzasidan qo‘shimcha izohlar va batafsil ma’lumotlar rasmiy '
    'kanallar orqali bosqichma-bosqich e’lon qilib boriladi. Fuqarolar yangiliklardan '
    'doimiy xabardor bo‘lib turishi mumkin.',

    'Kuzatuvchilarning ta’kidlashicha, ushbu yo‘nalishda qabul qilingan qarorlar amaliyotda '
    'o‘zining ijobiy natijasini ko‘rsata boshladi. Bu boradagi ishlar davom ettiriladi.',
]

QUOTE_POOL = [
    'Bugungi kunda eng muhimi — boshlangan ishlarni izchil va sifatli yakuniga yetkazish.',
    'Har bir qadam aholi manfaatini ko‘zlagan holda amalga oshirilmoqda.',
    'Natijalar raqamlarda emas, balki odamlarning kundalik hayotida seziladi.',
]


def img_tag(seed, caption):
    url = f'https://picsum.photos/seed/uzlife-{seed}/1000/560'
    return (
        f'<figure class="article__figure">'
        f'<img src="{url}" alt="{caption}" loading="lazy">'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>'
    )


class Command(BaseCommand):
    help = 'Yangiliklarning body maydoniga boy matn va ichki rasmlar qo‘shadi.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Allaqachon boyitilgan (HTML) maqolalarni ham qayta yozadi.')

    def handle(self, *args, **opts):
        updated = 0
        for art in Article.objects.select_related('category').all():
            if not opts['force'] and '<p>' in (art.body or ''):
                continue

            rnd = random.Random(art.pk)  # har bir maqola uchun izchil natija
            cat = art.category.name
            intro = INTRO.get(cat, DEFAULT_INTRO)

            paras = rnd.sample(BODY_POOL, k=4)
            quote = rnd.choice(QUOTE_POOL)

            parts = [f'<p><strong>{art.title}.</strong> {intro}</p>']
            parts.append(f'<p>{paras[0]}</p>')
            parts.append(f'<p>{paras[1]}</p>')
            # birinchi ichki rasm
            parts.append(img_tag(f'{art.pk}-a', f'{cat}: mavzuga oid tasvir'))
            parts.append(f'<blockquote>{quote}</blockquote>')
            parts.append(f'<p>{paras[2]}</p>')
            # ikkinchi ichki rasm
            parts.append(img_tag(f'{art.pk}-b', f'{art.title}'))
            parts.append(f'<p>{paras[3]}</p>')

            art.body = '\n'.join(parts)

            # qisqa mazmun ham to'ldirilsin
            if not art.summary or len(art.summary) < 60:
                art.summary = textwrap.shorten(intro + ' ' + paras[0], width=280,
                                               placeholder='…')

            art.save(update_fields=['body', 'summary'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {updated} ta yangilik boy matn va rasmlar bilan yangilandi.'
        ))
