from names_dataset import NameDataset
import numpy as np
import random
import openai
import time
import os
import shutil
from zhipuai import ZhipuAI
import json

# 在文件顶部添加智谱AI客户端
zhipu_client = ZhipuAI(api_key="2fbfc2acf9e54a09886d422966fa3448.lss3vj7BdP327Wdh")  # 替换为您的实际API密钥

def probability_threshold(threshold):
    '''
    Used in self.infect_interaction()
    '''
    #Generates random number from 0 to 1
    
    return (np.random.rand()<threshold)

def generate_qualifications(n: int):
    '''
    Returns a list of random educational qualifications.

    Parameters:
    n (int): The number of qualifications to generate.
    '''

    # Define a list of possible qualifications including lower levels and no education
    qualifications = ['No Education', 'Primary School', 'Middle School',
                      'High School Diploma', 'Associate Degree', 'Bachelor\'s Degree', 
                      'Master\'s Degree', 'PhD', 'Professional Certificate']

    # Randomly select n qualifications from the list
    generated_qualifications = random.choices(qualifications, k=n)

    return generated_qualifications


def generate_names(n: int, s: int, country_alpha2='US'):
    '''
    Returns random names as names for agents from top names in the USA
    Used in World.init to initialize agents
    '''

    # This function will randomly selct n names (n/2 male and n/2 female) without
    # replacement from the s most popular names in the country defined by country_alpha2
    if n % 2 == 1:
        n += 1
    if s % 2 == 1:
        s += 1

    nd = NameDataset()
    male_names = nd.get_top_names(s//2, 'Male', country_alpha2)[country_alpha2]['M']
    female_names = nd.get_top_names(s//2, 'Female', country_alpha2)[country_alpha2]['F']
    if s < n:
        raise ValueError(f"Cannot generate {n} unique names from a list of {s} names.")
    # generate names without repetition
    names = random.sample(male_names, k=n//2) + random.sample(female_names, k=n//2)
    del male_names
    del female_names
    random.shuffle(names)
    return names


def generate_big5_traits(n: int):
    '''
    Return big 5 traits for each agent
    Used in World.init to initialize agents
    '''

    #Trait generation
    agreeableness_pos=['Cooperation','Amiability','Empathy','Leniency','Courtesy','Generosity','Flexibility',
                        'Modesty','Morality','Warmth','Earthiness','Naturalness']
    agreeableness_neg=['Belligerence','Overcriticalness','Bossiness','Rudeness','Cruelty','Pomposity','Irritability',
                        'Conceit','Stubbornness','Distrust','Selfishness','Callousness']
    #Did not use Surliness, Cunning, Predjudice,Unfriendliness,Volatility, Stinginess

    conscientiousness_pos=['Organization','Efficiency','Dependability','Precision','Persistence','Caution','Punctuality',
                            'Punctuality','Decisiveness','Dignity']
    #Did not use Predictability, Thrift, Conventionality, Logic
    conscientiousness_neg=['Disorganization','Negligence','Inconsistency','Forgetfulness','Recklessness','Aimlessness',
                            'Sloth','Indecisiveness','Frivolity','Nonconformity']

    surgency_pos=['Spirit','Gregariousness','Playfulness','Expressiveness','Spontaneity','Optimism','Candor'] 
    #Did not use Humor, Self-esteem, Courage, Animation, Assertion, Talkativeness, Energy level, Unrestraint
    surgency_neg=['Pessimism','Lethargy','Passivity','Unaggressiveness','Inhibition','Reserve','Aloofness'] 
    #Did not use Shyness, Silenece

    emotional_stability_pos=['Placidity','Independence']
    emotional_stability_neg=['Insecurity','Emotionality'] 
    #Did not use Fear, Instability, Envy, Gullibility, Intrusiveness
    
    intellect_pos=['Intellectuality','Depth','Insight','Intelligence'] 
    #Did not use Creativity, Curiousity, Sophistication
    intellect_neg=['Shallowness','Unimaginativeness','Imperceptiveness','Stupidity']


    #Combine each trait
    agreeableness_tot = agreeableness_pos + agreeableness_neg
    conscientiousness_tot = conscientiousness_pos + conscientiousness_neg
    surgency_tot = surgency_pos + surgency_neg
    emotional_stability_tot = emotional_stability_pos + emotional_stability_neg
    intellect_tot = intellect_pos + intellect_neg

    #create traits list to be returned
    traits_list = []

    for _ in range(n):
        agreeableness_rand = random.choice(agreeableness_tot)
        conscientiousness_rand = random.choice(conscientiousness_tot)
        surgency_rand = random.choice(surgency_tot)
        emotional_stability_rand = random.choice(emotional_stability_tot)
        intellect_rand = random.choice(intellect_tot)

        selected_traits=[agreeableness_rand,conscientiousness_rand,surgency_rand,
                                emotional_stability_rand,intellect_rand]

        traits_chosen = (', '.join(selected_traits))
        traits_list.append(traits_chosen)
    del agreeableness_rand
    del conscientiousness_rand
    del surgency_rand
    del emotional_stability_rand
    del intellect_rand
    del selected_traits
    del traits_chosen
    return traits_list


def update_day(agent):
    '''
    Update day funtion to update day_sick
    Used in World.step()
    '''
    # print("Agent ID: {} Day infected: {}".format(agent.unique_id,agent.day_infected))


    #if person is healthy, no reason to update health status
    if agent.health_condition=="Susceptible" or agent.health_condition=="Infected":
        return

    if agent.health_condition=="to_be_infected":
        agent.health_condition="Infected"
        agent.model.daily_new_infected_cases +=1 #every time new infection occurs in a day, counter is updated
        agent.model.infected += 1 #Update amount infected at any given time
        agent.model.susceptible -= 1

    if agent.health_condition=="to_be_recover":
        agent.health_condition="Recovered"
        agent.model.daily_new_susceptible_cases +=1 #every time new infection occurs in a day, counter is updated
        agent.model.infected -= 1 #Update amount infected at any given time
        agent.model.susceptible += 1


def factorize(n):
    '''
    Factorize number for ideal grid dimensions for # of agents
    Used in World.init
    '''
    for i in range(int(n**0.5), 1, -1):
        if n % i == 0:
            return (i, n // i)
    return (n, 1)

def get_completion_from_messages(messages, model="glm-4", temperature=0):
    """使用智谱AI替代OpenAI API"""
    success = False
    retry = 0
    max_retries = 5 # 30 -> 5
    while retry < max_retries and not success:
        try:
            # 转换消息格式以适应智谱AI API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 调用智谱AI API
            response = zhipu_client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature
            )
            success = True
        except Exception as e:
            print(f"Error: {e}\nRetrying...")
            retry += 1
            time.sleep(0.5)

    if success:
        return response.choices[0].message.content
    else:
        return "无法获取响应，请检查API密钥或网络连接。"

def get_completion_from_messages_json(messages, model="glm-4", temperature=0):
    """使用智谱AI替代OpenAI API，并返回JSON格式的响应"""
    success = False
    retry = 0
    max_retries = 30
    while retry < max_retries and not success:
        try:
            # 转换消息格式以适应智谱AI API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 添加JSON格式要求到消息中
            formatted_messages.append({
                "role": "system",
                "content": "请以JSON格式返回响应，包含tweet、belief和reasoning字段。"
            })
            
            # 调用智谱AI API
            response = zhipu_client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature
            )
            success = True
        except Exception as e:
            print(f"Error: {e}\nRetrying...")
            retry += 1
            time.sleep(0.5)

    if success:
        content = response.choices[0].message.content
        # 尝试解析JSON，如果失败则格式化为JSON
        try:
            json.loads(content)
            return content
        except:
            # 如果返回的不是有效JSON，尝试提取并格式化
            try:
                # 查找可能的JSON部分
                if "{" in content and "}" in content:
                    json_part = content[content.find("{"):content.rfind("}")+1]
                    # 验证是否为有效JSON
                    json.loads(json_part)
                    return json_part
                else:
                    # 创建一个基本的JSON响应
                    return json.dumps({
                        "tweet": "无法解析响应，这是一个模拟的推文。",
                        "belief": 0,
                        "reasoning": "无法从模型获取有效的JSON响应。"
                    })
            except:
                # 创建一个基本的JSON响应
                return json.dumps({
                    "tweet": "无法解析响应，这是一个模拟的推文。",
                    "belief": 0,
                    "reasoning": "无法从模型获取有效的JSON响应。"
                })
    else:
        return json.dumps({
            "tweet": "无法获取响应，请检查API密钥或网络连接。",
            "belief": 0,
            "reasoning": "API调用失败。"
        })

def clear_cache():
    if os.path.exists("__pycache__"):
        shutil.rmtree("__pycache__")