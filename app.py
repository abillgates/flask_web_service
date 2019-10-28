# -*- coding: utf-8 -*-
import os
import time
import hashlib
import jpype

from flask import Flask, render_template, redirect, url_for, request, send_from_directory, make_response, send_file
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap

''' define 
'''
pubfile = "file_dir/pub_key"
mskfile = "file_dir/master_key"
prvfile = "file_dir/prv_key"
#inputfile = "file_dir/input.pdf"
#encfile = "file_dir/input.pdf.cpabe"
#decfile = "file_dir/input.pdf.new"
student_attr = "objectClass:inetOrgPerson objectClass:organizationalPerson " \
			 + "sn:student2 cn:student2 uid:student2 userPassword:student2 " \
			+ "ou:idp o:computer mail:student2@sdu.edu.cn title:student"
student_policy = "sn:student2 cn:student2 uid:student2 3of3"
#objectClass:inetOrgPerson objectClass:organizationalPerson sn:student2 cn:student2 uid:student2 userPassword:student2 ou:idp o:computer mail:student2@sdu.edu.cn title:student
app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'I have a dream'
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '\\upload_dir'
app.config['UPLOADED_DECPRV_DEST'] = os.getcwd() + '\\dec_dir'
app.config['UPLOADED_BACKUP_DEST'] = os.getcwd() + '\\backup_dir'
fileext={'xml', 'txt'}
app.config['UPLOADED_PHOTOS_ALLOW'] = fileext
app.config['UPLOADED_DECPRV_ALLOW'] = ['', 'cpabe']
#tuple('jpg jpe jpeg png gif svg bmp'.split())
photos = UploadSet('photos', fileext)
decprv = UploadSet('decprv')
backup = UploadSet('backup')
configure_uploads(app, [photos,decprv,backup])
patch_request_class(app)  # set maximum file size, default is 16MB


class UploadForm(FlaskForm):
    photo = FileField(validators = [FileAllowed(photos, u'Image Only!'), FileRequired(u'Choose a file!')])
    submit1 = SubmitField(u'Upload')


#FileAllowed(['jpg','png','gif'])]
class UploadForm_dec1(FlaskForm):
    prv = FileField(validators=[FileRequired(u'Choose a file!')])
    submit1 = SubmitField(u'Upload')


class UploadForm_dec2(FlaskForm):
    enc = FileField(validators=[FileRequired(u'Choose a file!')])
    submit2 = SubmitField(u'Upload')


class InputForm(FlaskForm):
    name = StringField('输入加密授权策略', validators=[DataRequired()])
    submit2 = SubmitField('input')


class KeygenForm(FlaskForm):
    name = TextAreaField(u'输入用户属性集合字符串', validators=[DataRequired()])
    submit = SubmitField('submit')


@app.route('/')
def index_page():
    return render_template('home.html')


@app.route('/enc', methods=['POST','GET'])
def enc_page():
    form1 = UploadForm()
    input_form = InputForm()
    #form1.submit1.data and
    if form1.submit1.data and form1.validate_on_submit():
        for filename in request.files.getlist('photo'):
            #name = hashlib.md5(('admin' + str(time.time())).encode("utf-8")).hexdigest()[:15]
            #photos.save(filename, name=name + '.')
            photos.save(filename)
            backup.save(filename)
        success = True

    else:
        success = False
    if input_form.submit2.data and input_form.validate_on_submit():
        input_str = input_form.name.data
        print(input_str)
        if not os.listdir(app.config['UPLOADED_PHOTOS_DEST']):
            return '<script>alert(" must first upload file ")</script>' \
                + render_template('index.html', form1=form1, input_form=input_form, success=success)
        else:
            files_name = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])[0]
            inputfile = files_name
            encfile = files_name + '.cpabe'
            py_enc(input_str, 'upload_dir\\' + inputfile, 'enc_dir\\' + encfile)
            directory = os.getcwd() + '\\enc_dir'
            return send_from_directory(directory, encfile, as_attachment=True)

    return render_template('index.html', form1=form1, input_form=input_form, success=success)


@app.route('/dec', methods=['POST','GET'])
def dec_page():
    folder = os.getcwd()+'\\dec_dir\\'
    prvform = UploadForm_dec1()
    encform = UploadForm_dec2()
    #isUpload = False
    if prvform.submit1.data and prvform.validate_on_submit():
        remove_file(app.config['UPLOADED_DECPRV_DEST'])
        privf = request.files['prv']
        decprv.save(privf, name='prv_file')
        isUpload = True
        print(isUpload)
    if encform.submit2.data and encform.validate_on_submit() and os.path.exists('dec_dir\\prv_file'):
        encf = request.files['enc']
        #encf.filename get the filename .cpabe
        en_fi_name=encf.filename
        decprv.save(encf)
        decfile = en_fi_name.rsplit('.',1)[0]
        print(decfile)
        py_dec(folder+'prv_file', folder+en_fi_name, folder+decfile)
        return send_from_directory(folder, decfile, as_attachment=True)
    return render_template('dec.html', prvform=prvform, encform=encform)


@app.route('/setup', methods=['POST','GET'])
def setup_page():
    py_setup()
    return '<script>alert("setup complete")</script>' \
        + '<a href='+url_for("index_page")+'>Index Page</a>'


@app.route('/keygen', methods=['POST','GET'])
def keygen_page():
    #prvfile
    keygenform = KeygenForm()
    if request.method == 'POST':
        attr = keygenform.name.data
        print(attr)
        #student_attr
        py_keygen(attr)
        #工作目录下的文件
        response = make_response(send_file(prvfile))
        response.headers["Content-Disposition"] = "attachment; filename=prv_key"
        return response
    return render_template('keygenpage.html',keygenform=keygenform)

'''
'''

@app.route('/manage')
def manage_file():
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    return render_template('manage.html', files_list=files_list)


@app.route('/open/<filename>')
def open_file(filename):
    file_url = photos.url(filename)
    file_path = photos.path(filename)
    print (file_path)
    #response = send_from_directory(file_path, filename, as_attachment=True)
    #print (response)
    response=make_response(send_file(file_path))
    return response
    return render_template('browser.html', file_url=file_url)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = photos.path(filename)
    os.remove(file_path)
    return redirect(url_for('manage_file'))


def init():
    # 启动JVM
    jvmPath = jpype.getDefaultJVMPath()
    # 加载jar包
    if not (jpype.isJVMStarted()):
        jpype.startJVM(jvmPath, "-ea", "-Djava.class.path=CP_ABE_RUN.jar")
    # 指定main class
    JDClass = jpype.JClass("cpabe.Cpabe")
    # 创建类实例对象
    jd = JDClass()
    return jd


def py_setup():
    # pubfile,mskfile
    remove_file('upload_dir\\')
    remove_file('enc_dir\\')
    Jc=init()
    # java functions setup
    Jc.setup(pubfile,mskfile)


def py_keygen(attr_str):
    #pubfile,prvfile,mskfile,
    Jc=init()
    Jc.keygen(pubfile, prvfile, mskfile, attr_str)


def py_enc(policy, inputfile, encfile):
    #pubfile, policy, inputfile, encfile
    Jc = init()
    Jc.enc(pubfile, policy, inputfile, encfile)


def py_dec(prvfile, encfile, decfile):
    # pubfile prvfile encfile decfile
    Jc = init()
    Jc.dec(pubfile, prvfile, encfile, decfile)


def remove_file(folder):
    files_list = os.listdir(folder)
    for fn in files_list:
        filepath = os.path.join(folder, fn)
        os.remove(filepath)
        print(str(filepath) + ' removed!')


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)