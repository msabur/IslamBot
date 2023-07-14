from collections import namedtuple
import random
import re

import discord
from discord.ext import commands

from quran.quran_info import *
from utils import utils
from utils.database_utils import ServerTranslation
from utils.errors import InvalidTranslation, respond_to_interaction_error
from utils.utils import convert_to_arabic_number, get_site_json

TOO_LONG = "This passage was too long to send."

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

CLEAN_HTML_REGEX = re.compile('<[^<]+?>\d*')

TranslationInfo = namedtuple('TranslationKey', ['id', 'fullname'])

# translatons no longer in quran.com api: 'suhel' (id 82), 'serbian' (id 215), 'georgian' (id 212)
translation_list = {
    'khattab': TranslationInfo(id=131, fullname="Dr. Mustafa Khattab, the Clear Quran"),  # English
    'bridges': TranslationInfo(id=149, fullname="Fadel Soliman, Bridges’ translation"),  # English
    'sahih': TranslationInfo(id=20, fullname="Saheeh International"),  # English
    'maarifulquran': TranslationInfo(id=167, fullname="Maarif-ul-Quran"),  # English
    'jalandhari': TranslationInfo(id=234, fullname="Fatah Muhammad Jalandhari"),  # Urdu
    'awqaf': TranslationInfo(id=78, fullname="Ministry of Awqaf, Egypt"),  # Russian
    'musayev': TranslationInfo(id=75, fullname="Alikhan Musayev"),  # Azeri
    'uyghur': TranslationInfo(id=76, fullname="Muhammad Saleh"),  # Uyghur
    'haleem': TranslationInfo(id=85, fullname="Abdul Haleem"),  # English
    'abuadel': TranslationInfo(id=79, fullname="Abu Adel"),  # Russian
    'karakunnu': TranslationInfo(id=80, fullname="Muhammad Karakunnu and Vanidas Elayavoor"),  # Malayalam
    'isagarcia': TranslationInfo(id=83, fullname="Sheikh Isa Garcia"),  # Spanish
    'divehi': TranslationInfo(id=86, fullname="Divehi"),  # Maldivian
    'burhan': TranslationInfo(id=81, fullname="Burhan Muhammad-Amin"),  # Kurdish
    'taqiusmani': TranslationInfo(id=84, fullname="Mufti Taqi Usmani"),  # English
    'ghali': TranslationInfo(id=17, fullname="Dr. Ghali"),  # English
    'hilali': TranslationInfo(id=203, fullname="Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan"),  # English
    'maududi.en': TranslationInfo(id=95, fullname="Tafheem-ul-Quran - Abul Ala Maududi"),  # English
    'transliteration': TranslationInfo(id=57, fullname="Transliteration"),
    'pickthall': TranslationInfo(id=19, fullname="English Translation (Pickthall)"),  # English
    'yusufali': TranslationInfo(id=22, fullname="Abdullah Yusuf Ali"),  # English
    'ruwwad': TranslationInfo(id=206, fullname="Ruwwad Center"),  # English
    'muhammadhijab': TranslationInfo(id=207, fullname="Dr. T. B. Irving"),  # English
    'junagarri': TranslationInfo(id=54, fullname="Maulana Muhammad Junagarhi"),  # Urdu
    'sayyidqutb': TranslationInfo(id=156, fullname="Fe Zilal al-Qur'an"),  # Urdu
    'mahmudhasan': TranslationInfo(id=151, fullname="Shaykh al-Hind Mahmud al-Hasan(with Tafsir E Usmani)"),  # Urdu
    'israrahmad': TranslationInfo(id=158, fullname="Bayan-ul-Quran"),  # Urdu
    'maududi': TranslationInfo(id=97, fullname="Tafheem e Qur'an - Syed Abu Ali Maududi"),  # Urdu
    'montada': TranslationInfo(id=136, fullname="Montada Islamic Foundation"),  # French
    'khawaja': TranslationInfo(id=139, fullname="Khawaja Mirof & Khawaja Mir"),  # Tajik
    'ryoichi': TranslationInfo(id=35, fullname="Ryoichi Mita"),  # Japanese
    'fahad.in': TranslationInfo(id=134, fullname="King Fahad Quran Complex"),  # Indonesian
    'piccardo': TranslationInfo(id=153, fullname="Hamza Roberto Piccardo"),  # Italian
    'taisirulquran': TranslationInfo(id=161, fullname="Taisirul Quran"),  # Bengali
    'mujibur': TranslationInfo(id=163, fullname="Sheikh Mujibur Rahman"),  # Bengali
    'rawai': TranslationInfo(id=162, fullname="Rawai Al-bayan"),  # Bengali
    'tagalog': TranslationInfo(id=211, fullname="Dar Al-Salam Center"),  # Tagalog
    'ukrainian': TranslationInfo(id=217, fullname="Dr. Mikhailo Yaqubovic"),  # Ukrainian
    'omar': TranslationInfo(id=229, fullname="Sheikh Omar Sharif bin Abdul Salam"),  # Tamil
    'bamoki': TranslationInfo(id=143, fullname="Muhammad Saleh Bamoki"),  # Kurdish
    'sabiq': TranslationInfo(id=141, fullname="The Sabiq company"),  # Indonesian
    'telegu': TranslationInfo(id=227, fullname="Maulana Abder-Rahim ibn Muhammad"),  # Telugu
    'marathi': TranslationInfo(id=226, fullname="Muhammad Shafi’i Ansari"),  # Marathi
    'hebrew': TranslationInfo(id=233, fullname="Dar Al-Salam Center"),  # Hebrew
    'gujarati': TranslationInfo(id=225, fullname="Rabila Al-Umry"),  # Gujarati
    'abdulislam': TranslationInfo(id=235, fullname="Malak Faris Abdalsalaam"),  # Dutch
    'ganda': TranslationInfo(id=232, fullname="African Development Foundation"),  # Ganda
    'khamis': TranslationInfo(id=231, fullname="Dr. Abdullah Muhammad Abu Bakr and Sheikh Nasir Khamis"),  # Swahili
    'thai': TranslationInfo(id=230, fullname="Society of Institutes and Universities"),  # Thai
    'kazakh': TranslationInfo(id=222, fullname="Khalifa Altay"),  # Kazakh
    'vietnamese': TranslationInfo(id=220, fullname="Ruwwad Center"),  # Vietnamese
    'siregar': TranslationInfo(id=144, fullname="Sofian S. Siregar"),  # Dutch
    'hasanefendi': TranslationInfo(id=88, fullname="Hasan Efendi Nahi"),  # Albanian
    'amharic': TranslationInfo(id=87, fullname="Sadiq and Sani"),  # Amharic
    'jantrust': TranslationInfo(id=50, fullname="Jan Trust Foundation"),  # Tamil
    'barwani': TranslationInfo(id=49, fullname="Ali Muhsin Al-Barwani"),  # Somali
    'swedish': TranslationInfo(id=48, fullname="Knut Bernström"),  # Swedish
    'khmer': TranslationInfo(id=128, fullname="Cambodian Muslim Community Development"),  # Khmer (Cambodian)
    'kuliev': TranslationInfo(id=45, fullname="Russian Translation ( Elmir Kuliev )"),  # Russian
    'diyanet': TranslationInfo(id=77, fullname="Turkish Translation(Diyanet)"),  # Turkish
    'turkish': TranslationInfo(id=77, fullname="Turkish Translation(Diyanet)"),  # Turkish
    'basmeih': TranslationInfo(id=39, fullname="Abdullah Muhammad Basmeih"),  # Malay
    'malay': TranslationInfo(id=39, fullname="Abdullah Muhammad Basmeih"),  # Malay
    'korean': TranslationInfo(id=219, fullname="Hamed Choi"),  # Korean (Hamed Choi)
    'finnish': TranslationInfo(id=30, fullname="Finnish"),  # Finnish
    'czech': TranslationInfo(id=26, fullname="Czech"),  # Czech
    'nasr': TranslationInfo(id=103, fullname="Helmi Nasr"),  # Portuguese
    'ayati': TranslationInfo(id=74, fullname="Tajik"),  # Tajik
    'mansour': TranslationInfo(id=101, fullname="Alauddin Mansour"),  # Uzbek
    'tatar': TranslationInfo(id=53, fullname="Tatar"),  # Tatar
    'romanian': TranslationInfo(id=44, fullname="Grigore"),  # Romanian
    'polish': TranslationInfo(id=42, fullname="Józef Bielawski"),  # Polish
    'norwegian': TranslationInfo(id=41, fullname="Norwegian"),  # Norwegian
    'amazigh': TranslationInfo(id=236, fullname="Ramdane At Mansour"),  # Amazigh
    'sindhi': TranslationInfo(id=238, fullname="Taj Mehmood Amroti"),  # Sindhi
    'chechen': TranslationInfo(id=106, fullname="Magomed Magomedov"),  # Chechen
    'bulgarian': TranslationInfo(id=237, fullname="Tzvetan Theophanov"),  # Bulgarian
    'yoruba': TranslationInfo(id=125, fullname="Shaykh Abu Rahimah Mikael Aykyuni"),  # Yoruba
    'shahin': TranslationInfo(id=124, fullname="Muslim Shahin"),  # Turkish
    'abduh': TranslationInfo(id=46, fullname="Mahmud Muhammad Abduh"),  # Somali
    'britch': TranslationInfo(id=112, fullname="Shaban Britch"),  # Turkish
    'maranao': TranslationInfo(id=38, fullname="Maranao"),  # Maranao
    'ahmeti': TranslationInfo(id=89, fullname="Albanian Translation"),  # Albanian
    'majian': TranslationInfo(id=56, fullname="Chinese Translation (Simplified) - Ma Jain"),  # Chinese
    'hausa': TranslationInfo(id=32, fullname="Hausa Translation(Abubakar Gumi)"),  # Hausa
    'nepali': TranslationInfo(id=108, fullname="Ahl Al-Hadith Central Society of Nepal"),  # Nepali
    'hameed': TranslationInfo(id=37, fullname="Malay Translation(Abdul Hameed and Kunhi)"),  # Malayalam
    'elhayek': TranslationInfo(id=43, fullname="Portuguese Translation( Samir )"),  # Portuguese
    'cortes': TranslationInfo(id=28, fullname="Spanish Translation(Cortes)"),  # Spanish
    'oromo': TranslationInfo(id=111, fullname="Ghali Apapur Apaghuna"),  # Oromo
    'french': TranslationInfo(id=31, fullname="Muhammad Hamidullah"),  # French
    'hamidullah': TranslationInfo(id=31, fullname="Muhammad Hamidullah"),  # French
    'persian': TranslationInfo(id=29, fullname="Hussein Taji Kal Dari"),  # Persian
    'farsi': TranslationInfo(id=29, fullname="Hussein Taji Kal Dari"),  # Persian
    'aburida': TranslationInfo(id=208, fullname="Abu Reda Muhammad ibn Ahmad"),  # German
    'othman': TranslationInfo(id=209, fullname="Othman al-Sharif"),  # Italian
    'baqavi': TranslationInfo(id=133, fullname="Abdul Hameed Baqavi"),  # Tamil
    'mehanovic': TranslationInfo(id=25, fullname="Muhamed Mehanović"),  # Bosnian
    'yazir': TranslationInfo(id=52, fullname="Elmalili Hamdi Yazir"),  # Turkish
    'zakaria': TranslationInfo(id=213, fullname="Dr. Abu Bakr Muhammad Zakaria"),  # Bengali
    'noor': TranslationInfo(id=199, fullname="Noor International Center"),  # Spanish
    'sato': TranslationInfo(id=218, fullname="Saeed Sato"),  # Japanese
    'sinhalese': TranslationInfo(id=228, fullname="Ruwwad Center"),  # Sinhala/Sinhalese
    'korkut': TranslationInfo(id=126, fullname="Besim Korkut"),  # Bosnian
    'umari': TranslationInfo(id=122, fullname="Maulana Azizul Haque al-Umari"),  # Hindi
    'assamese': TranslationInfo(id=120, fullname="Shaykh Rafeequl Islam Habibur-Rahman"),  # Assamese
    'sodik': TranslationInfo(id=127, fullname="Muhammad Sodik Muhammad Yusuf"),  # Uzbek
    'pashto': TranslationInfo(id=118, fullname="Zakaria Abulsalam"),  # Pashto
    'makin': TranslationInfo(id=109, fullname="Muhammad Makin"),  # Chinese
    'bubenheim': TranslationInfo(id=27, fullname="Frank Bubenheim and Nadeem"),  # German
    'indonesian': TranslationInfo(id=33, fullname="Indonesian Islamic affairs ministry"),  # Indonesian
}


class Translation:
    def __init__(self, key):
        self.id = self.get_translation_id(key)

    @staticmethod
    def get_translation_id(key):
        if key in translation_list:
            return translation_list[key].id

        translation = process.extract(key, translation_list.keys(), scorer=fuzz.partial_ratio, limit=1)
        if translation is None:
            raise InvalidTranslation

        return translation_list[translation[0][0]].id

    @staticmethod
    async def get_guild_translation(guild_id):
        guild_translation_handler = ServerTranslation(guild_id)
        translation_key = await guild_translation_handler.get()
        # Ensure we are not somehow retrieving an invalid translation
        try:
            Translation.get_translation_id(translation_key)
            return translation_key
        except InvalidTranslation:
            await guild_translation_handler.delete()
            return 'haleem'


class QuranRequest:
    def __init__(self, interaction: discord.Interaction, ref: str, is_arabic: bool, translation_key: str = None, reveal_order: bool = False):
        self.webhook = interaction.followup
        self.ref = QuranReference(ref=ref, allow_multiple_verses=True, reveal_order=reveal_order)
        self.is_arabic = is_arabic
        if translation_key is not None:
            self.translation = Translation(translation_key)

        self.regular_url = 'https://api.quran.com/api/v4/quran/translations/{}?verse_key={}:{}'
        self.arabic_url = 'https://api.quran.com/api/v4/quran/verses/uthmani?verse_key={}'
        self.verse_ayah_dict = {}

    async def get_verses(self):
        for ayah in self.ref.ayat_list:
            json = await get_site_json(self.regular_url.format(self.translation.id, self.ref.surah, ayah))
            text = json['translations'][0]['text']

            # Clear HTML tags
            text = re.sub(CLEAN_HTML_REGEX, ' ', text)

            # Truncate verses longer than 1024 characters
            if len(text) > 1024:
                text = text[0:1018] + " [...]"

            self.verse_ayah_dict[f'{self.ref.surah}:{ayah}'] = text

            # TODO: Don't fetch the translation name every time we fetch a verse.
            self.translation_name = json['meta']['translation_name']

    async def get_arabic_verses(self):
        for ayah in self.ref.ayat_list:
            json = await get_site_json(self.arabic_url.format(f'{self.ref.surah}:{ayah}'))
            text = json['verses'][0]['text_uthmani']

            # Truncate verses longer than 1024 characters
            if len(text) > 1024:
                text = text[0:1018] + " [...]"

            self.verse_ayah_dict[
                f'{convert_to_arabic_number(str(self.ref.surah))}:{convert_to_arabic_number(str(ayah))}'] = text

    def construct_embed(self):
        surah = Surah(self.ref.surah)
        if self.is_arabic:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f" سورة {surah.arabic_name}", icon_url=ICON)
        else:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f"Surah {surah.name} ({surah.translated_name})", icon_url=ICON)
            em.set_footer(text=f"Translation: {self.translation_name} | {surah.revelation_location}")

        if len(self.verse_ayah_dict) > 1:
            for key, text in self.verse_ayah_dict.items():
                em.add_field(name=key, value=text, inline=False)

            return em

        em.title = list(self.verse_ayah_dict)[0]
        em.description = list(self.verse_ayah_dict.values())[0]

        return em

    async def process_request(self):
        if self.is_arabic:
            await self.get_arabic_verses()
        else:
            await self.get_verses()

        em = self.construct_embed()
        if len(em) > 6000:
            await self.webhook.send(TOO_LONG)
        else:
            await self.webhook.send(embed=em)


class Quran(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = discord.app_commands.ContextMenu(
            name='Get Ayah from URL',
            callback=self.get_quran_ayah
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @discord.app_commands.command(name="quran", description="Send verses from the Qurʼān.")
    @discord.app_commands.describe(
        surah="The name or number of the surah to fetch, e.g. Al-Ikhlaas or 112",
        start_verse="The first verse to fetch, e.g. 255.",
        end_verse="The last verse to fetch if you want to send multiple verses, e.g. 260",
        translation="The translation to use",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def quran(self, interaction: discord.Interaction, surah: discord.app_commands.Transform[int, SurahNameTransformer], start_verse: int, end_verse: int = None,
                          translation: str = None, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        ref = start_verse if end_verse is None else f'{start_verse}-{end_verse}'
        if translation is None:
            translation = await Translation.get_guild_translation(interaction.guild_id)

        await QuranRequest(interaction=interaction, is_arabic=False, ref=f'{surah}:{ref}', translation_key=translation,
                           reveal_order=reveal_order).process_request()

    @discord.app_commands.command(name="aquran", description="تبعث آيات قرآنية في الشات")
    @discord.app_commands.describe(
        surah="اكتب رقم أو اسم السورة",
        start_verse="اكتب رقم أول آية",
        end_verse="اذا اردت ان تبعث اكثر من اية اكتب رقم اخر آية",
        reveal_order="هل السورة تشير إلى رقم أمر الوحي؟"
    )
    async def aquran(self, interaction: discord.Interaction, surah: discord.app_commands.Transform[int, SurahNameTransformer], start_verse: int, end_verse: int = None,
                           reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        ref = start_verse if end_verse is None else f'{start_verse}-{end_verse}'
        await QuranRequest(interaction=interaction, is_arabic=True, ref=f'{surah}:{ref}',
                           reveal_order=reveal_order).process_request()

    @discord.app_commands.command(name="rquran", description="Retrieve a random verse from the Qur'ān.")
    @discord.app_commands.describe(translation="The translation to use.")
    async def rquran(self, interaction: discord.Interaction, translation: str = None) -> None:
        await interaction.response.defer(thinking=True)
        surah = random.randint(1, 114)
        verse = random.randint(1, quranInfo['surah'][surah][1])

        if translation is None:
            translation = await Translation.get_guild_translation(interaction.guild_id)

        await QuranRequest(interaction=interaction, is_arabic=False, ref=f'{surah}:{verse}',
                           translation_key=translation).process_request()

    @discord.app_commands.command(name="raquran", description="Retrieve a random verse from the Qur'ān.")
    async def raquran(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        surah = random.randint(1, 114)
        verse = random.randint(1, quranInfo['surah'][surah][1])

        await QuranRequest(interaction=interaction, is_arabic=True, ref=f'{surah}:{verse}').process_request()

    @discord.app_commands.command(name="settranslation",
                                  description="Changes the default Qur'an translation for this server.")
    @discord.app_commands.describe(translation="The translation to use. See /help quran for a list.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.guild_only()
    async def set_translation(self, interaction: discord.Interaction, translation: str):
        await interaction.response.defer(thinking=True, ephemeral=True)

        translation_id = Translation.get_translation_id(translation)
        # this is so when giving success message, it says it sets it to the actual translation instead of user's typos
        # e.g user gives `khatab` but it will set it to `khattab` and tell the user the bot set it to `khattab`
        translation = list(translation_list.keys())[[v.id for v in translation_list.values()].index(translation_id)]
        await ServerTranslation(interaction.guild_id).update(translation)
        await interaction.followup.send(f":white_check_mark: **Successfully updated the default translation to `{translation}`!**")

    @quran.autocomplete('translation')
    @rquran.autocomplete('translation')
    @set_translation.autocomplete('translation')
    async def translation_autocomplete_callback(self, interaction: discord.Interaction, current: int):
        closest_matches = [match[0] for match in process.extract(current, [v.fullname for v in translation_list.values()], scorer=fuzz.partial_ratio, limit=5)]
        choices = [discord.app_commands.Choice(name=match, value=match) for match in closest_matches]
        return choices

    @discord.app_commands.command(name="surah", description="View information about a surah.")
    @discord.app_commands.describe(
        surah="The name or number of the surah, e.g. Al-Baqarah or 2.",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def surah(self, interaction: discord.Interaction, surah: discord.app_commands.Transform[int, SurahNameTransformer], reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        surah = Surah(num=surah, reveal_order=reveal_order)
        em = discord.Embed(colour=0x048c28)
        em.set_author(name=f'Surah {surah.name} ({surah.translated_name}) |  سورة {surah.arabic_name}', icon_url=ICON)
        em.description = (f'\n• **Surah number**: {surah.num}'
                          f'\n• **Number of verses**: {surah.verses_count}'
                          f'\n• **Revelation location**: {surah.revelation_location}'
                          f'\n• **Revelation order**: {surah.revelation_order} ')
        await interaction.followup.send(embed=em)

    async def get_quran_ayah(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True)
        url = utils.find_url('quran.com/', message.content)
        if url is None:
            return await interaction.followup.send("Could not find a valid `quran.com` link in this message.")
        try:
            meta = list(filter(None, url.split("/")))  # filter out the split url of the empty strings
            meta[-1] = meta[-1].split('?')[0]  # get rid of any parameters in the link
            meta = meta[2:]  # get rid of 'https' and 'quran.com' from the list
            meta = list(filter(None, meta))  # get rid of empty strings that may have stuck with us
            # This leaves us with either a list that is [surah:verse] or [surah, verse]

            if len(meta) == 1:  # for ['1:1']
                ref = meta[0]
            else:
                ref = f'{meta[0]}:{meta[1]}' # for ['1', '1']

            translation = await Translation.get_guild_translation(interaction.guild_id)
            return await QuranRequest(interaction=interaction, is_arabic=False, ref=ref, translation_key=translation).process_request()
        except:
            return await interaction.followup.send("Could not find a valid `quran.com` link in this message.")

    @quran.error
    @aquran.error
    @rquran.error
    @raquran.error
    @surah.error
    @set_translation.error
    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(Quran(bot))

