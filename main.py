import dash
from dash import dcc
from dash import html

import re
import spacy
import pymorphy2

import pytesseract

from textdistance import levenshtein as lev

from dash.dependencies import Input, Output

from googletrans import Translator


pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
nlp = spacy.load("en_core_web_lg")
nlp2 = spacy.load("ru_core_news_sm")
morph = pymorphy2.MorphAnalyzer()
idioms = ["by the skin of your teeth", "cry wolf", "play the devil's advocate", "up in the air", "A blessing in disguise", "Drive you up the wall" ]
translations = ["еле-еле", "бить ложную тревогу", "спорить ради обсуждения", "в подвешанном состоянии", "к лучшему", "раздражать"]
min_score = [5, 3, 3, 2, 2, 7]

app = dash.Dash(title="English lessons", suppress_callback_exceptions=True)
colors = {
   'background': '#FFE4C4'
}
app.layout = html.Div(style={'background-color': colors['background'], 'overflow-x': 'scroll'}, children=[
    html.H1('Write what do you want to translate:'),
    dcc.Textarea(
            id='translator_input',
            spellCheck=False,
            value='',
            name='text',
    ),
    html.Br(),
    html.Br(),
    html.Button('Translate', id='textarea-state-example-button', n_clicks=0),
    html.Br(),
    html.Br(),
    html.Div(id='translator_output'),
    dcc.Upload(
        id='upload-image',
        children=html.Div([
            html.A('Upload photo for translation')
        ]),
        multiple=True
    ),
    html.Div(id='output-image-upload'),
    html.Br(),
    html.Br(),
])

def translatorr(txt_inserted):
    txt_inserted = txt_inserted.lower()
    translator = Translator()
    if ((txt_inserted == '') or (txt_inserted.isspace())):
        return txt_inserted
    else:
        split_regex = re.compile(r'[.|!|?|…]')
        sentences = filter(lambda t: t, [t.strip() for t in split_regex.split(txt_inserted)])
        for sentence in sentences:
            tokens = sentence.split(' ')
            n = 0
            for phrase in idioms:
                score = 1000
                subseq = ''
                for i in range(len(tokens)):
                    if len(tokens) - i < 5:
                        k = len(tokens) - i
                    else:
                        k = 6
                    for j in range(i, i + k + 1):
                        subseqNew = ' '.join(tokens[i:j])
                        distance = lev.distance(phrase, subseqNew)
                        if distance < score:
                            score = distance
                            subseq = subseqNew
                if score <= min_score[n]:
                    sentenceNew = sentence
                    time = ''
                    textAnalisSen = nlp(sentence)
                    for word in textAnalisSen:
                        wordPosition = 1
                        if word.dep_ == 'nsubj' or word.dep_ == 'nsubjpass':
                            russianWord = translator.translate(word.text, src='en', dest='ru').text
                            gender = morph.parse(russianWord)[0].tag.gender
                            number = morph.parse(russianWord)[0].tag.number
                        elif word.dep_ == 'aux':
                            time = word.tag_
                            if time == 'MD' and word.text == 'will':
                                if number == 'sing':
                                    sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, 'будет')
                                else:
                                    sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, 'будут')
                            elif word.text != 'should' and word.text != 'must' and word.text != 'might' \
                                    and word.text != 'can' and word.text != 'could' and word.text != 'would'\
                                    and word.text != 'need' and word.text != 'let':
                                sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, '')
                        wordPosition = wordPosition + 1
                    translation = translations[n]
                    textAnalisSub = nlp(subseq)
                    for word1 in textAnalisSub:
                        if word1.pos_ == 'VERB':
                            tagVERB = word1.tag_
                            textAnalisTrans = nlp2(translation)
                            for word2 in textAnalisTrans:
                                if word2.pos_ == 'VERB':
                                    if tagVERB == 'VBD' or tagVERB == 'VBN'  or time == 'VBD' or time == 'VBN':
                                        wordChanged = morph.parse(word2.text)[0]
                                        if number == 'sing':
                                            if gender == 'femn':
                                                wordChanged = wordChanged.inflect({'past', 'femn'}).word
                                                translation = translation.replace(word2.text, wordChanged)
                                            else:
                                                wordChanged = wordChanged.inflect({'past', 'masc'}).word
                                                translation = translation.replace(word2.text, wordChanged)
                                        else:
                                            wordChanged = wordChanged.inflect({'past', 'plur'}).word
                                            translation = translation.replace(word2.text, wordChanged)

                    sentenceNew = sentenceNew.replace(subseq, translation)
                    txt_inserted = txt_inserted.replace(sentence, sentenceNew)
                n = n+1
        result = translator.translate(txt_inserted, src='en', dest='ru')
        return result.text

def parse_contents(contents: str, filename):
    b64_str = contents[contents.find(",")+1:]
    img = Image.open(BytesIO(base64.b64decode(b64_str)))
    txt_inserted = pytesseract.image_to_string(img)
    result = translatorr(txt_inserted)
    return html.Div(
        [
            html.H5(filename),
            html.Img(src=contents),
            html.Br(),
            html.H4("Текст на фото: "),
            html.H4(txt_inserted),
            html.Br(),
            html.H4("Перевод: "),
            html.H4(result),
            html.Hr(),
            ]
    )

@app.callback(Output('output-image-upload', 'children'),
              Input('upload-image', 'contents'),
              Input('upload-image', 'filename'))
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children

@app.callback(
    Output(component_id='translator_output', component_property='children'),
    Input(component_id='translator_input', component_property='value'),
)
def simple_translate(txt_inserted):
    return translatorr(txt_inserted)

if __name__ == '__main__':
   app.run_server(debug=True)