import botocore
import flask
import json
import markdown
import uuid

from email.message import EmailMessage

app = flask.Flask(__name__)

with open('stickers.json') as f:
    STICKERS = json.load(f)


@app.context_processor
def inject_stickers():
    return {'stickers': STICKERS}


@app.template_filter('markdown')
def markdown_filter(s):
    return markdown.markdown(s)


@app.route('/validate/<submission_id>', methods=('GET', 'POST'))
def validate(submission_id):
    raise NotImplementedError()


@app.route('/', methods=('GET', 'POST'))
def index():
    errors = []
    if flask.request.method == 'POST':
        total_requested = sum(int(flask.request.form.get(sticker, "0"))
                              for sticker in STICKERS)
        if total_requested < 1:
            errors.append("You didn't request any stickers!")
        elif total_requested > 15:
            errors.append("You requested too many stickers, don't be greedy")
        address = flask.request.form.getlist('address')
        if len(address) != 4:
            errors.append("How did you have not 4 address fields stop hacking")
        if not all(address[:3]):
            errors.append("The first three address fields are required")
        if not flask.request.form['email']:
            errors.append("You must provide an email")
        if not errors:
            ### hnng fucko the user filled out the form correctly
            submission_id = str(uuid.uuid4())
            data = {'email': flask.request.form['email']}
            data['address'] = address
            for sticker in STICKERS:
                data[sticker] = int(flask.request.form.get(sticker, "0"))

            session = botocore.session.get_session()
            s3 = session.create_client('s3')
            ses = session.create_client('ses')

            s3.put_object(
                Bucket='stickers-submissions-352b2c6b-d476-4ab5-8f84-83d9f455ccf9',
                Key=submission_id,
                Body=json.dumps(data),
                ContentType='text/plain')

            msg = EmailMessage()
            msg['Subject'] = 'Verify your stickers.wob.app request'
            msg['From'] = 'iliana@wobscale.website'
            msg['To'] = flask.request.form['email']
            msg.set_content("""Hello,

Somebody, hopefully you, requested some stickers to be sent to you!

Please validate your request at:
""" + flask.url_for('validate', submission_id=submission_id, _external=True))

            ses.send_raw_email(RawMessage={'Data': str(msg)})
            return ('A validation email has been sent to you ({}) with a link '
                    'you must click before stickers will be sent to you. &lt;3'
                    ).format(flask.request.form['email'])
    return flask.render_template('index.html',
                                 values=flask.request.form,
                                 errors=errors)
