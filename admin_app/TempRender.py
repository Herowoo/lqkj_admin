import xlrd
from xlutils.copy import copy

class TempRender:
    def __init__(self,temp_path):
        """
        :param temp_path: 模板路径
        """
        self.old_excel = xlrd.open_workbook(temp_path, formatting_info=True)
        self.old_ws=self.old_excel.sheets()[0]
        self.max_row = self.old_ws.nrows
        self.max_col = self.old_ws.ncols
        self.new_excel = copy(self.old_excel)
        # 获得第一个sheet的对象
        self.new_ws = self.new_excel.get_sheet(0)

    def render(self,kvs):
        """渲染"""
        render_data=[]
        end_row=0
        # new_col=0
        add_row=[0 for i in range(self.old_ws.nrows)]
        add_col = [0 for i in range(self.old_ws.ncols)]
        for i in range(self.max_col):
            temp=[]
            for j in range(self.max_row):
                value=self.old_ws.cell_value(j,i)
                if type(value)==str and ('$' in value or '#' in value):
                    # 渲染纵向列表
                    if '$[' in value and ']' in value:
                        key=value.replace('$[','').replace(']','')
                        if key in kvs:
                            #写渲染table列
                            self.render_write_down(j+add_col[i],i+add_row[j],kvs[key])
                            add_col[i]=len(kvs[key])-1
                            continue
                    # 渲染横向列表
                    if '#[' in value and ']' in value:
                        key = value.replace('#[', '').replace(']', '')
                        if key in kvs:
                            # 写渲染table行
                            self.render_write_right(j + add_col[i], i + add_row[j], kvs[key])
                            add_row[i] = len(kvs[key]) - 1

                            continue
                    #渲染sum函数
                    if '$sum(' in value and ')' in value:
                        key=value.replace('$sum(','').replace(')','')
                        if key in kvs:
                            self.new_ws.write(j + add_col[i], i+add_row[j], sum(kvs[key]))
                            continue
                #不渲染 直接填充
                if value:
                    self.new_ws.write(j + add_col[i], i + add_row[j], value)
                temp.append(value)
            render_data.append(temp)
        print(render_data)

    def render_write_right(self,pos_row,pos_col,data):
        """
        向右渲染写入excel
        :param pos_row: 
        :param pos_col: 
        :param data: 
        :return: 
        """
        print('渲染行',locals())
        for item in data:
            self.new_ws.write(pos_row,pos_col,item)
            pos_col+=1

    def render_write_down(self,pos_row,pos_col,data):
        """
        向下纵向渲染写入excel
        :param pos_row: 起始行位置
        :param pos_col: 起始列位置
        :param data: 
        :return: 
        """
        for item in data:
            self.new_ws.write(pos_row,pos_col,item)
            pos_row+=1


    def save(self,path):
        """保存文件"""
        self.new_excel.save(path)


if __name__=='__main__':
    tr=TempRender('temp.xls')
    kvs={
        'index':[1,2,3,4,5],
        'name':[ '陈志广', '魏改', '姚琼琼', '杨建涛', '姜晓旭'],
        'depart':['总经办', '财务部', '财务部', '企管部', '企管部'],
        'post':['总经理', '财务经理', '出纳', '主管', '人事专员'],
        'age':[1,2,3,4,5],
        'table_head':['序号','部门','职位','姓名','身份证号','年龄','民族','入职时间','学位',	'毕业学校','政治面貌','婚姻状况'	,'地址','个人电话','公司电话','邮箱']
    }
    tr.render(kvs)
    tr.save('render_result.xls')
