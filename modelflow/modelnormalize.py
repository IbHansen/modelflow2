# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 13:32:47 2020

@author: bruger
"""

from sympy import sympify, solve, Symbol
import re
from dataclasses import dataclass, field, asdict


from modelmanipulation import lagone, find_arg
from modelpattern import udtryk_parse
#%%
@dataclass
class Normalized_frml:
    ''' class defining result from normalization of expression'''
    original         : str = ''   
    preprocessed     : str = '' 
    normalized       : str = '' 
    calc_adjustment  : str = '' 
    
    def __str__(self):
        maxkey = max(len(k) for k in vars(self).keys())
        output = "\n".join([f'{k.capitalize():<{maxkey}} : {f}' for k,f in vars(self).items()])
        return output
    
    @property
    def fprint(self):
        print(f'\n{self}')
    
def endovar(f):
    '''Finds the first variable in a expression'''
    for t in udtryk_parse(f):
        if t.var:
            ud=t.var
            break
    return ud

def getclash(f):
    lhs_var = {t.var for t in udtryk_parse(f) if t.var }
    lhs_var_clash = {var : Symbol(var) for var in lhs_var}
    return lhs_var_clash

def funk_in(funk,a_string):
    '''Find the first location of a function in a string
    
    if found returns a match object where the group 2 is the interesting stuff used in funk_find_arg
    '''
    return re.search(fr'([^A-Z0-9_{{}}]|^)({funk})\(',a_string.upper(),re.MULTILINE) 
#%%
def funk_replace(funk1,funk2,a_string):
    '''
    replace funk1 with funk2 
    '''
    return re.sub(fr'([^A-Z0-9_{{}}]|^)({funk1})\(',fr'\1{funk2.upper()}(',a_string.upper(),re.MULTILINE) 

def funk_replace_list(replacelist,a_string):
    out_string = a_string[:]
    for funk1,funk2 in replacelist:
        out_string = funk_replace(funk1,funk2,out_string)
    return out_string 
        
    
funk_replace_list([('@D','DIFF'),('DLOG','DXLOG')],'d(a) = @d(v) x = dlog(y)')
#%%
funk_in('D','+d(b)'.upper())

def funk_find_arg(funk_match, streng):
    '''  chops a string in 3 parts \n
    1. before 'funk(' 

    2. in the matching parantesis 

    3. after the last matching parenthesis '''
    # breakpoint()
    start = funk_match.start(2)
    match = streng[funk_match.end(2):]
    open = 0
    for index in range(len(match)):
        if match[index] in '()':
            open = (open + 1) if match[index] == '(' else (open - 1)
        if not open:
            return streng[:start], match[1:index], match[index + 1:]


 
def preprocess(udtryk,funks=[]):
    '''
    test processing expanding dlog,diff,movavg,pct,logit functions 

    Args:
        udtryk (str): model we want to do template expansion on 
        funks (list, optional): list of user defined functions . Defaults to [].

    Returns:
        None.

    has to be changed to (= for when the transition to 3.8 is finished. 

    '''
    udtryk_up = udtryk.upper().replace(' ','')
    while  funk_in('DLOG',udtryk_up):
         dlog_match = funk_in('DLOG',udtryk_up)   # change this in 3.8
         fordlog,dlogudtryk_up,efterdlog=funk_find_arg(dlog_match,udtryk_up)
         udtryk_up=fordlog+'DIFF(LOG('+dlogudtryk_up+'))'+efterdlog           
    while  funk_in('LOGIT',udtryk_up):
         logit_match = funk_in('LOGIT',udtryk_up)
         forlogit,logitudtryk_up,efterlogit=funk_find_arg(logit_match,udtryk_up)
         udtryk_up=forlogit+'(LOG('+logitudtryk_up+'/(1.0 -'+logitudtryk_up+')))'+efterlogit 
         
    while  funk_in('MOVAVG', udtryk_up):
         movavg_match = funk_in('MOVAVG', udtryk_up)
         forkaede,kaedeudtryk,efterkaede=funk_find_arg(movavg_match,udtryk_up)
         arg=kaedeudtryk.split(',',1)
         avg='(('
         term=arg[0]
         #print(arg,len(arg)/2)
         # breakpoint()
         antal=int(arg[1])
         for i in range(antal):
             avg=f'{avg}{term}+'
             term=lagone(term,funks=funks)
         avg=avg[:-1]+')/'+str(antal)+'.0)'
         udtryk_up=forkaede+avg+efterkaede 
     
    while  funk_in('PCT',udtryk_up):
        pct_match = funk_in('PCT',udtryk_up)
      # pc(expression) -->100 * (var/var(-1)-1)udtryk_up
        forpc,pcudtryk,efterpc=funk_find_arg(pct_match,udtryk_up)
        udtryk_up=f'{forpc} (100 * ( ({pcudtryk}) / ({lagone(pcudtryk,funks=funks)}) -1)) {efterpc}'           

#          
    while  funk_in('DIFF' , udtryk_up):
        diff_match = funk_in('DIFF' , udtryk_up)
        fordif,difudtryk_up,efterdif=funk_find_arg(diff_match,udtryk_up)
        udtryk_up=fordif+'(('+difudtryk_up+')-('+lagone(difudtryk_up+'',funks=funks)+'))'+efterdif  
         
    return udtryk_up         
 
        
def normal(ind_o,the_endo='',add_adjust=True,do_preprocess = True):
    '''
    normalize an expression g(y,x) = f(y,x) ==> y = F(x,z)
    
    Default find the expression for the first variable on hthe left hand side (lhs)
    
    The variable - without lags-  should not be on rhs. 
    
    
    

    Args:
        ind_o (str): input expression
        the_endo (str, optional): the endogeneous to isolate on the left hans side. if '' the first variable in the lhs. It shoud be on the left hand side. 
        add_adjust (TYPE, optional): force introduction aof adjustment term, and an expression to calculate it
        do_preprocess (TYPE, optional): DESCRIPTION. preprocess the expression

    Returns:
         An instance of the class: Normalized_frml here you will find the different relevant expressions 

    '''    
    preprocessed = preprocess(ind_o) if do_preprocess else ind_o[:]
    ind = preprocessed.upper().replace('LOG(','log(').replace('EXP(','exp(')
    lhs,rhs=ind.strip().split('=',1)
    lhs = lhs.strip()
    if len(udtryk_parse(lhs)) >=2: # we have an expression on the left hand side 
        clash = getclash(ind)
        
        endo_name = the_endo.upper() if the_endo else endovar(lhs)
        endo = sympify(endo_name,clash)
        a_name = f'{endo_name}_A' if add_adjust else ''
        kat=sympify(f'Eq({lhs},__rhs__ {"+" if add_adjust else ""}{a_name})',clash)  
        
        endo_frml  = solve(kat,endo  ,simplify=False,rational=False)
        res_rhs    = str(endo_frml[0]).replace('__rhs__',f' ({rhs.strip()}) ')
        out_frml   = f'{endo} = {res_rhs}'.upper()
        
        if add_adjust:
            a_sym = sympify(a_name,clash)
            a_frml     = solve(kat,a_sym,simplify=False,rational=False)
            res_rhs_a  = str(a_frml[0]).replace('__rhs__',f' ({rhs.strip()}) ')
            out_a      = f'{a_name} = {res_rhs_a}'.upper()
        else:
            out_a = ''
        
        result = Normalized_frml(ind_o,preprocessed,out_frml,out_a) 
        
        return result
    else: # no need to solve this equation 
        if add_adjust:
            result = Normalized_frml(ind_o,preprocessed,f'{lhs} = {rhs} + {lhs}_A', f'{lhs}_A = ({rhs})-({lhs})')
        else:
            result = Normalized_frml(ind_o,preprocessed,f'{lhs} = {rhs}')
        return result
    
        
if __name__ == '__main__':
    
    normal('dlog  ( a) = 42 * b',add_adjust=1).fprint
    normal('a = n(-1)',add_adjust=0).fprint
    normal('PCT(a) = n(-1)',add_adjust=0).fprint
    normal('a = movavg(pct(b),2)',add_adjust=0).fprint
    normal('pct(c) = z',add_adjust=0).fprint
    normal('pct(c) = movavg(pct(b),2)',add_adjust=0).fprint