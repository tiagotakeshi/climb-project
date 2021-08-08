import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import plotly.express as px
from geopy.geocoders import Nominatim
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import DBSCAN

st.set_page_config(layout='wide')

@st.cache(allow_output_mutation=True)
def get_data(path):
    database = pd.read_csv(path, encoding='utf=16')

    return database


def final_df(database):
    database.drop_duplicates(inplace=True)
    auxiliar = database[['grade_id', 'climb_type', 'lat', 'long']]

    return auxiliar


def alg_dbscan(dataset_alg):
    scaler = MinMaxScaler()
    X = pd.DataFrame(scaler.fit_transform(dataset_alg.values), columns=dataset_alg.columns, index=dataset_alg.index)
    clustering = DBSCAN(eps=0.03, min_samples=10).fit(X)
    labels = clustering.labels_
    dataset_alg['cluster'] = labels

    return dataset_alg, labels


def overview_data(dataset, df, grades):
    header_container = st.beta_container()
    form_container = st.beta_container()

    with header_container:
        st.image('header.png')

        st.title("A new way to find climbing spots")
        st.header("Welcome!")

    with form_container:
        st.subheader("Please, to help you finding new climbing places, we need you to fill in some information after "
                     "reading this instructions:")

        st.text("We need a few informations about grades and location to show some recomendations.\n\n"

                "Follow the steps below:\n\n"

                '1 - Check if the side bar is expanded, otherwise click in the icon ">" on the top in the rigth side\n\n'

                '2 - Select the Type of Climbing (Route or Boulder)\n\n'

                '3 - Informe the city where you want to discovery new climbing spots nearby. Follow the example below.\n'

                '    Ex: "City Name, Country" ; Ex. 2: "Pindamonhangaba, Brazil"\n\n'

                '4 - Select the difficult grade. The difficults grades for Routes follows the French graduation, and the '
                'Boulder grades follows the USA graduation.\n\n'

                'If all the steps are clear then click on the Checkbox below to start:\n\n')

        agreed_check = st.checkbox(label="I Understanded all the steps")

        if agreed_check:

            climbtype_selectbox = st.sidebar.selectbox(
                "Which modality would you like to search?",
                ("Route", "Boulder")
            )
            location = st.sidebar.text_input(label="City and Country: ")
            if climbtype_selectbox == 'Route':
                grade = st.sidebar.selectbox(label="Please, insert the difficult grade desired",
                                             options=['4b', '4c', '5a', '5b', '5c', '6a', '6a+', '6b',
                                                      '6b+', '6c', '6c+', '7a', '7a+', '7b', '7b+',
                                                      '7c', '7c+', '8a', '8a+', '8b', '8b+', '8c', '8c+',
                                                      '9a', '9a+'])

                grade_id = int(grades[grades['fra_routes'] == grade]['id'].head(1))
                climbtype = 0

            else:
                grade = st.sidebar.selectbox(label="Please, insert the difficult grade desired",
                                             options=['V0', 'V1', 'V2', 'V3', 'V3/V4', 'V4', 'V4/V5',
                                                      'V5', 'V5/V6', 'V6', 'V7', 'V8', 'V8/V9', 'V10',
                                                      'V11', 'V12', 'V13', 'V14', 'V15', 'V16'])

                grade_id = int(grades[grades['usa_boulders'] == grade]['id'].head(1))
                climbtype = 1

            sm = st.sidebar.checkbox("Show in Map")
            lr = st.sidebar.checkbox("Show the list result")
            ss = st.sidebar.checkbox("Show statistics")

            if st.sidebar.button('Find'):
                with st.spinner('Wait for it...'):
                    aux = []
                    info = {}
                    try:
                        local = Nominatim(user_agent='climb_study').geocode(location)
                        info['lat'] = local.latitude
                        info['long'] = local.longitude
                    except:
                        info['lat'] = ''
                        info['long'] = ''
                    aux.append(info)
                    geo = pd.DataFrame(aux)

                    user = {
                        'grade_id': grade_id,
                        'climb_type': climbtype,
                        'lat': geo['lat'],
                        'long': geo['long']
                    }
                    user_info = pd.DataFrame(user)
                    #st.dataframe(user_info)
                    df_user = df.append(user_info, sort=False)
                    df_user.reset_index(inplace=True)
                    df_user.drop(columns='index', inplace=True)
                    aux, label = alg_dbscan(df_user)
                    nro_cluster = int(aux.tail(1).cluster)

                    if nro_cluster == -1:
                        st.error("We can't find any places to reccomend! Try in another location.")

                    else:
                        label = label[0:-1]
                        dataset['cluster'] = label
                        selected_cluster = dataset[dataset['cluster'] == nro_cluster]
                        if sm:
                            density_map = folium.Map(location=[selected_cluster['lat'].mean(), selected_cluster['long'].mean()],
                                                     zoom_start=5)

                            marker_cluster = MarkerCluster().add_to(density_map)
                            for name, row in selected_cluster.iterrows():
                                folium.Marker([row['lat'], row['long']],
                                              popup='{0}'.format(row['name'])).add_to(marker_cluster)


                            folium_static(density_map)

                        if lr:
                            if climbtype == 0:
                                st.dataframe(selected_cluster[['name','crag','city','grade_route']])

                            else:
                                st.dataframe(selected_cluster[['name', 'crag', 'city', 'grade_boulder']])

                        if ss:
                            st.text("Result: {0}".format(len(selected_cluster['name'])))
                            if climbtype == 0:
                                st.text("Grade(s): {0}".format(selected_cluster['grade_route'].unique()))
                                fig = px.bar(x=selected_cluster['grade_route'])
                            else:
                                st.text("Grade(s): {0}".format(selected_cluster['grade_boulder'].unique()))
                                fig = px.bar(x=selected_cluster['grade_boulder'])
                            st.plotly_chart(fig, use_container_width=True)

                if nro_cluster != -1:
                    st.success('Done!')

    return None


if __name__ == '__main__':
    #ETL
    # Extraction
    dataset_path = 'dataset/final_climbing_dataset.csv'
    dataset = get_data(dataset_path)
    df = final_df(dataset)

    grades_path = 'dataset/final_grades_results.csv'
    grades = get_data(grades_path)


    # Transformation

    overview_data(dataset, df, grades)


    # Loading


